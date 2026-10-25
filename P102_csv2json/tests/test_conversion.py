"""Pruebas de validacion y del contrato de exportacion."""

import json
import runpy
from pathlib import Path

import pytest


MODULE = runpy.run_path(str(Path(__file__).resolve().parents[1] / "src/main.py"))
convert_csv_to_json = MODULE["convert_csv_to_json"]


def test_export_only_required_columns_and_preserve_unicode(tmp_path):
    source = tmp_path / "drivers.csv"
    source.write_text(
        'driverId,name,certified,wage-plan,ssn,location,extra\n'
        '10,"Sanchez, Jose\u0301",Y,miles,123,Address,private\n',
        encoding="utf-8",
    )
    destination = tmp_path / "nested" / "drivers.json"

    records = convert_csv_to_json(source, destination)

    assert json.loads(destination.read_text(encoding="utf-8")) == [
        {
            "driverId": "10",
            "name": "Sanchez, Jose\u0301",
            "certified": "Y",
            "wage-plan": "miles",
        }
    ] == records


@pytest.mark.parametrize(
    "contents",
    [
        "",
        "driverId,name,name,certified,wage-plan\n",
        "driverId,name\n10,Name\n",
        "driverId,name,certified,wage-plan\n10,Name,Y\n",
        "driverId,name,certified,wage-plan\n10,Name,Y,miles,extra\n",
    ],
)
def test_reject_invalid_csv_without_overwriting_output(tmp_path, contents):
    source = tmp_path / "drivers.csv"
    source.write_text(contents, encoding="utf-8")
    destination = tmp_path / "drivers.json"
    destination.write_text("[]", encoding="utf-8")

    with pytest.raises(ValueError):
        convert_csv_to_json(source, destination)

    assert destination.read_text(encoding="utf-8") == "[]"
