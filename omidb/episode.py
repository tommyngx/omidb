import datetime
from dataclasses import dataclass, fields, field
from typing import Optional, List, Dict
import enum
from .events import Events, SideOpinion
from .study import Study
from .lesion import Lesion


@enum.unique
class Type(enum.Enum):
    """Type of episode"""

    CA = "Continued Assessment"
    CD = "Delayed Treatment"
    CF = "Follow-up after treatment"
    CI = "Interval case"
    CR = "Local Recurrence"
    F = "First Call"
    G = "GP Referral"
    H = "Higher Risk"
    N = "Non-rout Recall"
    R = "Routine Recall"
    S = "Self Referral"
    X = "Other"


@enum.unique
class Action(enum.Enum):
    """Episode action"""

    EC = "Early Recall for Clinic"
    ES = "Early Recall for Screening"
    FN = "Fine Needle Aspiration"
    FP = "Follow-up (Post-treatment)"
    FV = "Further X-ray views"
    IP = "Inpatient biopsy"
    MT = "Medical Treatment"
    NA = "No Action from this procedure"
    R2 = "Routine second film opinion (obsolete)"
    RC = "Review in clinic"
    RF = "Referral to consultant/GP"
    RR = "Routine recall for screening"
    ST = "Surgical Treatment"
    TR = "Repeat Film (technical)"
    WB = "Wide Bore Needle"


@enum.unique
class Status(enum.Enum):
    """
    Summarises the status of an episode according to the event opinions
    and the episode type. Does not consider the properties of any other episode.
    """

    CI = "Interval Cancer"
    M = "Malignant"
    B = "Benign"
    NAB = "Normal with assessment and biopsy"
    NA = "Normal with assessment"
    N = "Normal"


@dataclass
class Episode:
    """
    An episode contains a set of medical procedures or events associated with
    the treatment or diagnosis of a clinical condition. Medical imaging studies
    are included with each episode, and are typically (but not always) linked
    to one or more events.

    :param id: NBSS episode identifier, only unique within client
    :param events: A set of medical procedures associated with the episode
    :param studies: List of :class:`omidb.study.Study` s where collections of
        screening and diagnostic images reside
    :param type: Enumeration defining the type of episode
    :param action: Enumeration defining the action outcome of the episode
    :param opened_date: Date that the episode opened
    :param closed_date: Date that the episode closed
    :param diagnosis_date: Date that the interval cancer (if applicable) was diagnosed
    :param is_closed: boolean signifying whether the episode is closed
    :param lesions: A list of :class:`omidb.lesion.Lesion` s, examined in the
        episode
    :param actual_opened_year: True year that the episode was opened.
    """

    id: str
    events: Optional[Events] = None
    studies: List[Study] = field(default_factory=list)
    type: Optional[Type] = None
    action: Optional[Action] = None
    opened_date: Optional[datetime.date] = None
    closed_date: Optional[datetime.date] = None
    diagnosis_date: Optional[datetime.date] = None
    is_closed: Optional[bool] = None
    lesions: Dict[str, Lesion] = field(default_factory=dict)
    actual_opened_year: Optional[int] = None

    @property
    def has_benign_opinions(self) -> bool:
        """
        Returns ``True`` if the container ``e.events`` contains a
        :class:`omidb.events.Events.surgery` or
        :class:`omidb.events.Events.biopsy_wide` or
        :class:`omidb.events.Events.biopsy_fine` or where the left or right
        opinion is benign (:class:`omidb.events.SideOpinion.OB`)
        """

        if self.events is None:
            return False

        for event in (
            self.events.surgery,
            self.events.biopsy_wide,
            self.events.biopsy_fine,
        ):
            if event is not None and (
                event.left_opinion == SideOpinion.OB
                or event.right_opinion == SideOpinion.OB
            ):
                return True

        return False

    @property
    def has_malignant_opinions(self) -> bool:
        """
        Returns ``True`` if the container ``e.events`` contains a
        :class:`omidb.events.Events.surgery` or
        :class:`omidb.events.Events.biopsy_wide` or
        :class:`omidb.events.Events.biopsy_fine` or where the left or right
        opinion is malignant (:class:`omidb.events.SideOpinion.OM`)
        """

        if self.events is None:
            return False

        for event in (
            self.events.surgery,
            self.events.biopsy_wide,
            self.events.biopsy_fine,
        ):
            if event is not None and (
                event.left_opinion == SideOpinion.OM
                or event.right_opinion == SideOpinion.OM
            ):
                return True

        return False

    @property
    def is_interval_cancer(self) -> bool:
        """
        Return ``True`` if:
            ``episode.type`` is ``omidb.episode.Type.CI``
            ``episode.has_malignant_opinions`` evaluates to ``True``
        Return ``False`` otherwise.
        """

        if self.type != Type.CI:
            return False

        if self.has_malignant_opinions:
            return True

        if self.events is not None:
            for event in (
                self.events.surgery,
                self.events.biopsy_wide,
                self.events.biopsy_fine,
            ):
                if event is not None:
                    return False
        return True

    @property
    def status(self) -> Optional[Status]:
        if self.is_interval_cancer:
            return Status.CI
        if self.type == Type.CI:
            return None
        if self.has_malignant_opinions:
            return Status.M
        if self.has_benign_opinions:
            return Status.B
        if (
            self.events is None
            or not _validate_events(self)
            or self.events.surgery is not None
        ):
            return None
        if self.events.assessment is not None:
            if (
                self.events.biopsy_fine is not None
                or self.events.biopsy_wide is not None
            ):
                return Status.NAB
            else:
                return Status.NA
        return Status.N


def _validate_events(e: Episode) -> bool:
    """
    If any non-screening event contains null opinions, returns ``False``.

    This is to protect against any 'null' events that imply the patient
    underwent more than just a screening examination and the outcome is
    unknown.
    """
    if e.events is None:
        return True
    for fd in fields(e.events):
        event = getattr(e.events, fd.name)
        if event is None:
            continue

        if fd.name == "screening":
            continue

        if event.left_opinion is None and event.right_opinion is None:
            return False
    return True
