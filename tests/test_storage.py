import mongomock
import pytest

from pdf_search.storage import MongoStorage


@pytest.fixture
def storage():
    return MongoStorage(client=mongomock.MongoClient())


def test_empty_storage(storage):
    assert storage.load() == {}


def test_save_and_load(storage):
    documents = {
        "/pdfs/first.pdf": {
            "signature": [120, 1000],
            "text": "Охрана труда",
        }
    }

    storage.save(documents)

    assert storage.load() == documents


def test_update_document(storage):
    storage.save({
        "/pdfs/first.pdf": {
            "signature": [120, 1000],
            "text": "Старый текст",
        }
    })

    updated = {
        "/pdfs/first.pdf": {
            "signature": [150, 2000],
            "text": "Новый текст",
        }
    }

    storage.save(updated)

    assert storage.load() == updated
    assert storage.collection.count_documents({}) == 1


def test_delete_missing_document(storage):
    storage.save({
        "/pdfs/first.pdf": {
            "signature": [120, 1000],
            "text": "Первый документ",
        },
        "/pdfs/second.pdf": {
            "signature": [150, 2000],
            "text": "Второй документ",
        },
    })

    storage.save({
        "/pdfs/second.pdf": {
            "signature": [150, 2000],
            "text": "Второй документ",
        }
    })

    assert list(storage.load()) == ["/pdfs/second.pdf"]


def test_delete_all_documents(storage):
    storage.save({
        "/pdfs/first.pdf": {
            "signature": [120, 1000],
            "text": "Первый документ",
        }
    })

    storage.save({})

    assert storage.load() == {}
