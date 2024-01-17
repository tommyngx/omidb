import pathlib
import tempfile
import omidb
import pytest
from collections import namedtuple


Dirs = namedtuple("Dirs", "root omidb data images")


@pytest.fixture
def dirs():

    with tempfile.TemporaryDirectory() as root_dir:
        root = pathlib.Path(root_dir)
        omidb_dir = root / "omidb"
        data_dir = omidb_dir / "data"
        images_dir = omidb_dir / "images"

        omidb_dir.mkdir()
        data_dir.mkdir()
        images_dir.mkdir()

        yield Dirs(root, omidb_dir, data_dir, images_dir)


def test_missing_data_dir_raise(dirs: Dirs):
    dirs.data.rmdir()
    with pytest.raises(FileNotFoundError) as e:
        assert omidb.DB(dirs.data / "nodir")


def test_find_client_dirs(dirs: Dirs):
    clients = set(["demd1", "demd2", "optm3", "nonsense"])
    for client in clients:
        (dirs.data / client).mkdir()

    parser = omidb.DB(dirs.data)
    clients.remove("nonsense")
    assert parser.clients == clients


def test_parse_study_dir(monkeypatch, mocker, dirs: Dirs):
    client = "demd1"
    studies = ["1.2.3.4567", "nonsense"]
    for study in studies:
        study_dir = dirs.data / "demd1" / study
        study_dir.mkdir(parents=True)
        print(study_dir)

    def mock(self, client, studies):
        return client, set(studies)

    mocker.patch("omidb.DB._parse_client", mock)
    parser = omidb.DB(dirs.data)
    expected = set([studies[0]])
    for parsed_client, parsed_studies in parser:
        assert client == parsed_client
        assert expected == parsed_studies
