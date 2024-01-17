import pydicom
import matplotlib
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable
from .mark import Mark


@dataclass
class LoaderParams:
    client_id: str
    study_id: str
    series_id: str
    image_id: str


DicomLoaderFunc = Callable[[LoaderParams], pydicom.dataset.FileDataset]
JsonLoaderFunc = Callable[[LoaderParams], Dict[str, Any]]


@dataclass
class DicomLoader:
    args: LoaderParams
    func: DicomLoaderFunc


@dataclass
class JsonLoader:
    args: LoaderParams
    func: JsonLoaderFunc


@dataclass
class Image:
    """
    Container for a mammogram, stored in the DICOM_ format. An image can have
    zero or more marks for one or many lesions.

    :param id: SOP Instance UID, a unique identifier
    :param dcm_path: Path to the dicom image
    :param json_path: Path to the JSON file storing DICOM metadata
    :param marks: A list of marks or annotations, represented by
        :class:`omidb.mark.Mark`

    .. _DICOM: https://www.dicomstandard.org/
    """

    id: str
    dcm_loader: Optional[DicomLoader] = None
    json_loader: Optional[JsonLoader] = None
    marks: List[Mark] = field(default_factory=list)
    _dcm: Optional[pydicom.FileDataset] = None
    _json: Optional[Dict[str, Any]] = None

    @property
    def dcm(self) -> Optional[pydicom.FileDataset]:
        """
        Returns a :class:`pydicom.dataset.FileDataset`, representing a parsed DICOM file
        """
        if not self._dcm and self.dcm_loader is not None:
            self._dcm = self.dcm_loader.func(self.dcm_loader.args)
        return self._dcm

    @property
    def attributes(self) -> Optional[Dict[str, Any]]:
        """
        Access DICOM metadata via the JSON representation
        """

        if not self._json and self.json_loader is not None:
            self._json = self.json_loader.func(self.json_loader.args)
        return self._json

    def plot(
        self, ax: Optional[matplotlib.axes.Axes] = None
    ) -> Optional[matplotlib.image.AxesImage]:
        """
        Plot the dicom
        """

        if self.dcm is None:
            return None

        if not ax:
            fig, ax = plt.subplots()

        return ax.imshow(self.dcm.pixel_array, cmap=plt.cm.bone)
