import enum
from dataclasses import dataclass, field
import datetime
from typing import List, Optional


@enum.unique
class Opinion(enum.Enum):
    """Opinion after a procedure"""

    A1 = "Assess normal"
    A2 = "Assess benign"
    A3 = "Assess uncert'n"
    A4 = "Assess suspic"
    A5 = "Assess malig"
    B1 = "Unsatis/Normal"
    B2 = "Benign"
    B3 = "Benign unc mal"
    B4 = "Susp of malig"
    B5 = "Malignant"
    BA = "Clinical"
    C1 = "Cyt unsatis"
    C2 = "Cyt benign"
    C3 = "Cyt atypia"
    C4 = "Cyt susp malig"
    C5 = "Cyt malig"
    H0 = "Hist unreported"
    H1 = "Histol normal"
    H2 = "Histol benign"
    H5 = "Hist malignant"
    I1 = "Imaging normal"
    I2 = "Imaging benign"
    I3 = "Imaging uncertain"
    I4 = "Imaging suspicious"
    I5 = "Imaging malig"
    MRI1 = "MRI normal"
    MRI2 = "MRI benign"
    MRI3 = "MRI indeterminate"
    MRI4 = "MRI suspicious"
    MRI5 = "MRI malig"
    OB = "O Benign"
    OM = "O Malignant"
    ON = "O Normal"
    OS = "O Suspicious"
    OU = "O Uncertain"
    P1 = "Clin normal"
    P2 = "Clin benign"
    P3 = "Clin uncertain"
    P4 = "Clin suspicious"
    P5 = "Clin malignant"
    R1 = "Rad normal"
    R2 = "Rad benign"
    R3 = "Rad uncertain"
    R4 = "Rad suspicious"
    R5 = "Rad malig"
    RB = "R Benign"
    RM = "R Malignant"
    RN = "R Normal"
    RO = "R Unreported"
    RS = "R Suspicious"
    RU = "R Uncertain"
    SH = "History suspic"
    U1 = "USS normal"
    U2 = "USS benign"
    U3 = "USS uncertain"
    U4 = "USS suspicious"
    U5 = "USS malig"


@enum.unique
class SideOpinion(enum.Enum):
    """Side-specific opinion"""

    OB = "Benign"
    OM = "Malignant"
    ON = "Normal"
    OS = "Suspicious"
    OU = "Uncertain"


@enum.unique
class Event(enum.Enum):
    """Type of event. Corresponds to the fields of :class:`omidb.events.Events`"""

    assessment = "assessment"
    biopsy_fine = "biopsy_fine"
    biopsy_wide = "biopsy_wide"
    clinical = "clinical"
    screening = "screening"
    surgery = "surgery"


@dataclass
class BaseEvent:
    """
    Generic NBSS information pertaining to a medical procedure.

    :param left_opinion: Code summarising the diagnosis of the left breast
    :param right_opinion: Code summarising the diagnosis of the right breast
    :param dates: Dates extracted from left and right lesion data
    """

    left_opinion: Optional[SideOpinion] = None
    right_opinion: Optional[SideOpinion] = None
    dates: List[datetime.date] = None


@dataclass
class BreastScreeningData:
    """
    Side-specific breast-screening data.

    :param date: Date that the examination took place
    :param equipment_make_model: Short description of the equipment used for
        the examination. Typically the manufacturer of the imaging device.
    :param opinion: Enumeration representing the opinion code
    """

    date: Optional[datetime.date] = None
    equipment_make_model: Optional[str] = None
    opinion: Optional[Opinion] = None


@dataclass
class Screening(BaseEvent):
    """
    NBSS information pertaining to a screening procedure.

    :param left: Screening information for the left breast
    :param right: Screening information for the right breast
    """

    left: Optional[BreastScreeningData] = None
    right: Optional[BreastScreeningData] = None


@dataclass
class Events:
    """
    A collection of events, for a given :class:`omidb.core.Episode`.
    """

    screening: List[Screening] = field(default_factory=list)
    assessment: Optional[BaseEvent] = None
    clinical: Optional[BaseEvent] = None
    biopsy_wide: Optional[BaseEvent] = None
    biopsy_fine: Optional[BaseEvent] = None
    surgery: Optional[BaseEvent] = None
