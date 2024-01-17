from typing import List
from dataclasses import dataclass
import matplotlib
import matplotlib.pyplot as plt
from .image import Image


@dataclass
class Series:
    """
    A collection of images taken during one examination by one modality, for a
    given position of the patient on the acquisition device. In Full-Field
    Digital Mammography, each image is typically associated with one unique
    series.

    :param id: Series Instance UID, a unique identifier
    :param images: A list of :class:`Image` objects for the examination
    """

    id: str
    images: List[Image]

    @property
    def num_images(self) -> int:
        """
        The number of images in this series
        """
        return len(self.images)

    def plot(self) -> matplotlib.pyplot.Axes:
        """
        Convenience method for plotting all images in the series
        """

        if self.num_images == 1:
            return self.images[0].plot()

        fig, axes = plt.subplots(1, self.num_images)

        for i, image in enumerate(self.images):
            image.plot(axes[i])

        return axes
