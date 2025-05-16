from pathlib import Path

import pytest

from app.loaders import load_dataset
from app.validators import validate_dataset


@pytest.mark.parametrize(
    "folder, expected_ok",
    [
        ("data", True),
        ("tests/bad_data", False),
    ],
)
def test_dataset_validation(folder, expected_ok):
    data = load_dataset(Path(folder))
    errors = validate_dataset(data)

    if expected_ok:
        assert errors == []
    else:
        assert errors, "Se esperaba que el dataset tuviera errores"
        locs = [e.loc for e in errors]
        assert any(("requisitos" in loc) or ("notas" in loc) for loc in locs)
