from __future__ import annotations
from typing import Dict, List, Callable, Iterator, Union
from .client import Client
from .episode import Episode
from .study import Study
from .series import Series
from .image import Image


class FilterImages:
    """
    Filter images of a hierarchical Image model, by applying a user-specified
    filtering function to each image.

    :param image_filter: Use `image_filter` to filter images provided by the caller.
    """

    def __init__(self, image_filter: Callable[[Image], bool]):
        self.image_filter = image_filter

    @classmethod
    def dicom_filter(cls, tag_criteria: Dict[str, List[str]]) -> FilterImages:
        """
        Returns a new :class:`FilterImages` instance whose filter function uses the
        tag/attribute name of a Data Element to filter images by the value of a
        specific Data Element, i.e. filter by dicom property.

        :param tag_criteria: Dictionary whose keys are the data element tags
            and values are a list of data element values
        """

        def the_filter(image: Image) -> bool:
            ds = image.dcm

            if ds is None:
                raise ValueError(f"Failed to load DICOM for image {image.id}")

            for tag, value in tag_criteria.items():
                v = ds.data_element(tag)
                if v is not None and v.value not in value:
                    return False

            return True

        return cls(the_filter)

    def _from_client_iter(self, client: Client) -> Iterator[Episode]:
        """
        Iterate over episodes within `client`
        """
        for episode in client.episodes:
            for _ in self._from_episode_iter(episode):
                yield (_)

    def _from_episode_iter(self, episode: Episode) -> Iterator[Study]:
        """
        Iterate over studies within `episode`
        """
        if episode.studies:
            for study in episode.studies:
                for _ in self._from_study_iter(study):
                    yield (_)

    def _from_study_iter(self, study: Study) -> Iterator[Series]:
        """
        Iterate over series within `study`
        """
        for series in study.series:
            yield (series)

    def __call__(self, obj: Union[Client, Episode, Study, Series]) -> None:
        """
        Inplace filtering of the :class:`omidb.image.Image` s found in ``obj``.

        :param obj: Filter the images nested within one of the core OMI-DB objects
        """

        if isinstance(obj, Series):
            obj.images = [_ for _ in filter(self.image_filter, obj.images)]

        elif isinstance(obj, Client):
            for _ in self._from_client_iter(obj):
                self(_)

        elif isinstance(obj, Episode):
            for _ in self._from_episode_iter(obj):
                self(_)

        elif isinstance(obj, Study):
            for _ in self._from_study_iter(obj):
                self(_)
