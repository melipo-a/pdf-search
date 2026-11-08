import json
import logging
import math
import re
import shlex
from collections import Counter
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError


def words(text):
    return re.findall(r"[^\W_]+", text.lower())


def load_directories(config_path):
    config_path = Path(config_path).resolve()
    directories = []
    started = False
    inline = False

    for line in config_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if not started:
            if not line.startswith("directories:"):
                raise ValueError("Некорректный файл конфигурации")

            started = True
            value = line[len("directories:"):].strip()

            if not value or value.startswith("#"):
                continue

            match = re.fullmatch(r"\[(.*)\](?:\s+#.*)?", value)

            if match is None:
                raise ValueError("Некорректный файл конфигурации")

            inline = True
            parser = shlex.shlex(match.group(1), posix=True)
            parser.whitespace = ","
            parser.whitespace_split = True
            parser.commenters = ""

            try:
                paths = [path.strip() for path in parser]
            except ValueError as error:
                raise ValueError(
                    "Некорректный файл конфигурации"
                ) from error

            for path in paths:
                if not path:
                    raise ValueError("Не указан путь к каталогу")

                directories.append(
                    (config_path.parent / path).resolve()
                )

            continue

        if inline or not line.startswith("- "):
            raise ValueError("Некорректный файл конфигурации")

        try:
            parts = shlex.split(line[2:], comments=True)
        except ValueError as error:
            raise ValueError(
                "Некорректный путь к каталогу"
            ) from error

        folder = " ".join(parts).strip()

        if not folder:
            raise ValueError("Не указан путь к каталогу")

        directories.append(
            (config_path.parent / folder).resolve()
        )

    if not directories:
        raise ValueError("Не указаны каталоги поиска")

    return directories


def extract_pdf_text(filename):
    reader = PdfReader(str(filename))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


class PDFSearch:
    def __init__(self, config_path, cache_path=None, storage=None):
        self.config_path = Path(config_path).resolve()
        self.directories = load_directories(self.config_path)
        self.storage = storage

        if cache_path is None:
            cache_path = self.config_path.parent / ".pdf_index.json"

        self.cache_path = Path(cache_path)
        self.documents = []
        self.vectors = []
        self.idf = {}

        self.update_index()

    def update_index(self):
        if self.storage is not None:
            old_cache = self.storage.load()
        else:
            try:
                old_cache = json.loads(
                    self.cache_path.read_text(encoding="utf-8")
                )
            except (FileNotFoundError, json.JSONDecodeError):
                old_cache = {}

        if not isinstance(old_cache, dict):
            old_cache = {}

        new_cache = {}
        documents = []
        found = set()

        used_labels = set()
        all_names = {folder.name for folder in self.directories}
        labels = []

        for folder in self.directories:
            label = folder.name
            number = 2

            if label in used_labels:
                while (
                    f"{label}_{number}" in used_labels
                    or f"{label}_{number}" in all_names
                ):
                    number += 1

                label = f"{label}_{number}"

            labels.append(label)
            used_labels.add(label)

        for folder, label in zip(self.directories, labels):
            if not folder.is_dir():
                raise FileNotFoundError(f"Каталог не найден: {folder}")

            for filename in sorted(folder.rglob("*")):
                if not filename.is_file():
                    continue

                if filename.suffix.lower() != ".pdf":
                    continue

                absolute = str(filename.resolve())

                if absolute in found:
                    continue

                found.add(absolute)
                info = filename.stat()
                signature = [info.st_size, info.st_mtime_ns]
                cached = old_cache.get(absolute, {})

                if not isinstance(cached, dict):
                    cached = {}

                if (
                    cached.get("signature") == signature
                    and isinstance(cached.get("text"), str)
                ):
                    text = cached["text"]
                else:
                    try:
                        text = extract_pdf_text(filename)
                    except (PdfReadError, OSError) as error:
                        logging.warning(
                            "Не удалось прочитать %s: %s",
                            filename,
                            error,
                        )
                        continue

                new_cache[absolute] = {
                    "signature": signature,
                    "text": text,
                }

                display_path = filename.relative_to(folder).as_posix()

                if len(self.directories) > 1:
                    display_path = f"{label}/{display_path}"

                documents.append({
                    "file": display_path,
                    "counts": Counter(words(text)),
                })

        if self.storage is not None:
            self.storage.save(new_cache)
        else:
            self.cache_path.write_text(
                json.dumps(new_cache, ensure_ascii=False),
                encoding="utf-8",
            )

        self.documents = documents
        self._build_vectors()

    def _build_vectors(self):
        size = len(self.documents)
        frequency = Counter()

        for document in self.documents:
            frequency.update(document["counts"].keys())

        self.idf = {
            word: math.log((size + 1) / (count + 1)) + 1
            for word, count in frequency.items()
        }

        self.vectors = [
            self._vector(document["counts"])
            for document in self.documents
        ]

    def _vector(self, counts):
        weights = {
            word: count * self.idf[word]
            for word, count in counts.items()
            if word in self.idf
        }

        norm = math.sqrt(
            sum(weight ** 2 for weight in weights.values())
        )

        if not norm:
            return {}

        return {
            word: weight / norm
            for word, weight in weights.items()
        }

    def search(self, query):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Укажите поисковый запрос")

        query_vector = self._vector(Counter(words(query)))
        results = []

        for document, vector in zip(self.documents, self.vectors):
            score = sum(
                weight * vector.get(word, 0)
                for word, weight in query_vector.items()
            )

            if score > 0:
                results.append((score, document["file"]))

        results.sort(key=lambda item: (-item[0], item[1]))

        return [
            {"file": filename}
            for _, filename in results[:10]
        ]
