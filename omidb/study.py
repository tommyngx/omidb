from typing import Optional, List
from dataclasses import dataclass, field
import datetime
from .events import Event
from .series import Series


@dataclass
class Study:
    """
    An imaging examination comprising a number of series, each containing a set
    of images.

    :param id: Study Instance UID, a unique identifier
    :param series: A list of :class:`omidb.series.Series`' containing a set of
        mammograms
    :param date: Date of the examination
    :param event_type: Enumerations defining the medical procedures associated
        with the study
    """

    id: str
    series: List[Series]
    date: Optional[datetime.date] = None
    event_type: List[Event] = field(default_factory=list)
