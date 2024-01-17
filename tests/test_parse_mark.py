import pytest
import omidb
from collections import namedtuple
import tempfile
import pathlib
from typing import Iterator


mark_data = {
    "ArchitecturalDistortion": "ArchitecturalDistortion",
    "BenignClassification": "coarse_or_popcorn-like",
    "Conspicuity": "Subtle",
    "Dystrophic": "Dystrophic",
    "FatNecrosis": "FatNecrosis",
    "FocalAsymmetry": "FocalAsymmetry",
    "Height": "240",
    "LesionID": 6711,
    "LinkedNBSSLesionNumber": "1,2",
    "MarkID": 10241,
    "Mass": 1,
    "MassClassification": "spiculated",
    "MilkOfCalcium": "MilkOfCalcium",
    "OtherBenignCluster": "OtherBenignCluster",
    "PlasmaCellMastitis": "PlasmaCellMastitis",
    "Skin": "Skin",
    "SuspiciousCalcifications": "SuspiciousCalcifications",
    "SutureCalcification": "SutureCalcification",
    "Vascular": "Vascular",
    "Width": "327",
    "WithCalcification": "WithCalcification",
    "X1": "756",
    "X2": "1183",
    "Y1": "1487",
    "Y2": "1733",
}


Dirs = namedtuple("Dirs", "root omidb data images")


@pytest.fixture
def dirs() -> Iterator[Dirs]:

    with tempfile.TemporaryDirectory() as root_dir:
        root = pathlib.Path(root_dir)
        omidb_dir = root / "omidb"
        data_dir = omidb_dir / "data"
        images_dir = omidb_dir / "images"

        omidb_dir.mkdir()
        data_dir.mkdir()
        images_dir.mkdir()

        yield Dirs(root, omidb_dir, data_dir, images_dir)


def test_parse_mark(dirs: Dirs) -> None:

    parser = omidb.client_parser.ClientParser("", {}, {}, [], False)

    mark = parser._parse_mark(mark_data)

    assert mark.architectural_distortion
    assert mark.benign_classification == omidb.mark.BenignClassification.coarse
    assert mark.conspicuity == omidb.mark.Conspicuity.subtle
    assert mark.dystrophic_calcification
    assert mark.fat_necrosis
    assert mark.focal_asymmetry
    assert mark.id == str(mark_data["MarkID"])
    assert mark.lesion_ids == set(["1", "2"])
    assert mark.milk_of_calcium
    assert mark.other_benign_cluster
    assert mark.plasma_cell_mastitis
    assert mark.benign_skin_feature
    assert mark.suspicious_calcifications
    assert mark.suture_calcification
    assert mark.vascular_feature
    assert mark.calcifications

    assert mark.boundingBox.x1 == int(mark_data.get("X1", 0))
    assert mark.boundingBox.x2 == int(mark_data.get("X2", 0))
    assert mark.boundingBox.y1 == int(mark_data.get("Y1", 0))
    assert mark.boundingBox.y2 == int(mark_data.get("Y2", 0))
