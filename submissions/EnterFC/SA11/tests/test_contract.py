import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.contract import validate_batch, validate_page


@pytest.fixture
def page():
    return {
        "source": "03-rotated-table.pdf",
        "page": 1,
        "method": "ocr",
        "text": "Таблица",
        "tables": [{"columns": ["Название", "Значение"], "rows": [["Итого", "12"]]}],
        "uncertainty": ["Проверить число"],
    }


def test_valid_page_and_separate_document_error(page):
    assert validate_page(page) is None
    assert (
        validate_batch(
            {
                "pages": [page],
                "errors": [
                    {"source": "04-broken.pdf", "error": "Повреждён", "continued": True}
                ],
            }
        )
        is None
    )


@pytest.mark.parametrize("invalid", [None, 0, True, -1, 1.5, "1"])
def test_rejects_missing_or_invalid_page_number(page, invalid):
    if invalid is None:
        del page["page"]
    else:
        page["page"] = invalid
    with pytest.raises(ValueError):
        validate_page(page)


def test_rejects_error_mixed_into_success(page):
    page["error"] = "Ошибка"
    with pytest.raises(ValueError):
        validate_page(page)
    with pytest.raises(ValueError):
        validate_batch({"pages": [page], "errors": []})


@pytest.mark.parametrize(
    "field,value",
    [
        ("source", ""),
        ("method", ""),
        ("text", None),
        ("tables", {}),
        ("uncertainty", [42]),
        ("tables", [{"columns": ["A"], "rows": [[1]]}]),
        ("tables", [{"columns": ["A"], "rows": "bad"}]),
    ],
)
def test_rejects_invalid_page_fields(page, field, value):
    page[field] = value
    with pytest.raises(ValueError):
        validate_page(page)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"pages": [], "errors": {}},
        {
            "pages": [],
            "errors": [{"source": "04-broken.pdf", "error": "bad", "continued": False}],
        },
        {
            "pages": [],
            "errors": [{"source": "04-broken.pdf", "error": "bad", "continued": 1}],
        },
        {
            "pages": [],
            "errors": [
                {
                    "source": "04-broken.pdf",
                    "error": "bad",
                    "continued": True,
                    "page": 1,
                }
            ],
        },
    ],
)
def test_rejects_malformed_batch_or_error(payload):
    with pytest.raises(ValueError):
        validate_batch(payload)
