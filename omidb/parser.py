import re
import pathlib
import json
from typing import List, Dict, Optional, Iterator, Any, Sequence, Union
from loguru import logger
import pydicom
from .image import LoaderParams
from .client import Client
from .client_parser import ClientParser


class DB:
    """
    OMI-DB parser

    :param data_dir: Root directory of the OMI-DB data directory.
    :param image_dir: Root directory of the OMI-DB image directory.
    :param ignore_missing_images: If ``True``, the existence of dicom images
        belonging to a series will not be checked: parsing is based entirely on the
        JSON representations of the DICOM headers. Set to ``False`` to parse only
        those images for which you have *both* JSON and DICOM files for.
    :param clients: Only parse these clients, if they exist
    :param exclude_clients: Exclude these clients, even if they are in ``clients``
    :param distinct_event_study_links: Only match events to imaging studies
        when distinct (1 to 1 mapping)
    :param nbss_dir: An alternative data dir where nbss files can be found
    """

    def __init__(
        self,
        data_dir: Union[str, pathlib.Path],
        image_dir: Optional[Union[str, pathlib.Path]] = None,
        ignore_missing_images: bool = True,
        clients: Optional[Sequence[str]] = None,
        exclude_clients: Optional[Sequence[str]] = None,
        distinct_event_study_links: bool = True,
        nbss_dir: Optional[Union[str, pathlib.Path]] = None,
    ):
        self.alternative_nbss_dir = None if nbss_dir is None else pathlib.Path(nbss_dir)
        self.ignore_missing_images = ignore_missing_images
        self.distinct_event_study_links = distinct_event_study_links

        self._image_dir = (
            pathlib.Path() if image_dir is None else pathlib.Path(image_dir)
        )
        self._data_dir = pathlib.Path(data_dir)

        if not self._data_dir.is_dir():
            raise FileNotFoundError(f"Directory {data_dir} not found")

        if not clients:
            clients = []
            for client_path in self._data_dir.glob("*"):
                if client_path.is_dir() and client_path.name[:4] in ("demd", "optm"):
                    clients.append(client_path.name)

        self.clients = set(clients)

        if exclude_clients:
            self.clients = set(clients) - set(exclude_clients)

    def __iter__(self) -> Iterator[Client]:
        """
        Iterates over all parsable clients found in the OMI-DB directory.

        :return: client_it: A :class:`omidb.client.Client` iterator
        """
        for client in self.clients:
            _data_dir = self._data_dir / client
            studies: List[str] = []
            for study in _data_dir.glob("*/**"):
                # Extract study ID from path
                if study.is_dir():
                    match = re.match(r"\d+.", study.name)
                    if match:
                        studies.append(study.name)

            try:
                yield self._parse_client(client, studies)
            except Exception:
                logger.exception(f"Failed to parse {client}, skipping")
                continue

    def _parse_client(self, client_id: str, studies: List[str]) -> Client:
        imagedb = self._imagedb(client_id)
        nbss = self._nbss(client_id)

        client = ClientParser(
            client_id,
            nbss,
            imagedb,
            studies,
            self.distinct_event_study_links,
            self._json_loader,
            self._dcm_loader,
        )()

        return client

    def _nbss_path(self, client_id: str) -> pathlib.Path:
        """Path of the NBSS json file corresponding to the client with ID
        `client_id`
        """

        if self.alternative_nbss_dir is not None:
            data_dir = self.alternative_nbss_dir
        else:
            data_dir = self._data_dir

        p1 = data_dir / client_id / ("nbss_" + client_id + ".json")

        if not p1.exists():
            p1 = data_dir / client_id / ("NBSS_" + client_id + ".json")

        return p1

    def _nbss(self, client_id: str) -> Dict[str, Any]:
        """NBSS data corresponding to the client with ID `client_id`"""

        with open(self._nbss_path(client_id)) as f:
            nbss: Dict[str, Any] = json.load(f)
        return nbss

    def _imagedb(self, client_id: str) -> Dict[str, Any]:
        """IMAGEDB data corresponding to the client with ID `client_id`"""

        p1 = self._data_dir / client_id / ("imagedb_" + client_id + ".json")

        if not p1.exists():
            p1 = self._data_dir / client_id / ("IMAGEDB_" + client_id + ".json")

        with open(p1) as f:
            imagedb: Dict[str, Any] = json.load(f)

        return imagedb

    def _dcm_loader(self, p: LoaderParams) -> pydicom.dataset.FileDataset:
        dcm_path = self._image_dir / p.client_id / p.study_id / (p.image_id + ".dcm")
        return pydicom.dcmread(str(dcm_path))

    def _json_loader(self, p: LoaderParams) -> Dict[str, Any]:
        json_path = self._data_dir / p.client_id / p.study_id / (p.image_id + ".json")
        # Due to inconsistency in file naming
        if not json_path.exists():
            json_path = json_path.with_suffix(".dcm.json")

        result: Dict[str, Any] = {}
        with open(json_path) as f:
            result = json.load(f)
        return result
