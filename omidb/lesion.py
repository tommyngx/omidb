import datetime
import itertools
from typing import List, Optional, Union
from dataclasses import dataclass, field
from .events import Opinion
import enum


Side = enum.Enum("Side", "L R")

Status = enum.Enum("Status", "Invasive Insitu")


@enum.unique
class LesionDescription(enum.Enum):
    AS = "Asymmetry"
    CA = "Calcification only"
    CY = "Cyst"
    DS = "Distortion"
    LN = "Lymph node"
    MA = "Mass"
    MC = "Mass with calcification"
    NA = "No significant abnormality"
    ZZ = "Clinical abnormality"


def _lesion_positions() -> List[str]:
    result = ["LM", "RM"]
    for pos in itertools.product("LR", "ABCDE", "1234"):
        result.append("".join(pos))
    return result


LesionPosition = enum.Enum("LesionPosition", _lesion_positions())  # type: ignore


@enum.unique
class LocalisationType(enum.Enum):
    S = "Skin Marker"
    U = "Ultrasound Guidance"
    X = "X-Ray Guidance"


@enum.unique
class SiteIndicator(enum.Enum):
    M = "Multiple"
    S = "Single"


@enum.unique
class InvasiveCarcinomaComponent(enum.Enum):
    IDC = "Ductal/NST"
    ILC = "Lobular"
    IMC = "Medullary like"
    IMU = "Mucinous"
    IPX = "Other component"
    ITC = "Tubular/cribriform"


@enum.unique
class HistologicalGrade(enum.Enum):
    G1 = "I"
    G2 = "II"
    G3 = "III"
    NA = "Not assessable"


@enum.unique
class InvasiveCarcinomaType(enum.Enum):
    IN = "Ductal/NST"
    IP = "Pure Special Type"
    IM = "Mixed"
    IO = "Other"


@enum.unique
class InSituCarcinomaComponent(enum.Enum):
    NID = "Ductal"
    NIL = "Lobular"
    NIP = "Paget’s"


@enum.unique
class DCISGrade(enum.Enum):
    NDH = "High"
    NDI = "Intermediate"
    NDL = "Low"
    NDN = "Not assessable"


@enum.unique
class MalignancyType(enum.Enum):
    a = "In-situ"
    b = "Invasive"
    c = "Not assessable"


@dataclass
class LesionAssessment:
    date: Optional[datetime.date] = None


@dataclass
class LesionSurgery:
    date: Optional[datetime.date] = None
    invasive_components: List[InvasiveCarcinomaComponent] = field(default_factory=list)
    disease_grade: Optional[HistologicalGrade] = None
    invasive_type: Optional[InvasiveCarcinomaType] = None
    insitu_components: List[InSituCarcinomaComponent] = field(default_factory=list)
    dcis_grade: Optional[DCISGrade] = None
    opinion: Optional[Opinion] = None


@dataclass
class LesionBiopsyWide:
    date: Optional[datetime.date] = None
    invasive_components: List[InvasiveCarcinomaComponent] = field(default_factory=list)
    disease_grade: Optional[HistologicalGrade] = None
    invasive_type: Optional[InvasiveCarcinomaType] = None
    insitu_components: List[InSituCarcinomaComponent] = field(default_factory=list)
    dcis_grade: Optional[DCISGrade] = None
    malignant_type: Optional[MalignancyType] = None
    opinion: Optional[Opinion] = None


@dataclass
class LesionBiopsyFine:
    date: Optional[datetime.date] = None
    opinion: Optional[Opinion] = None


@dataclass
class LesionIntervalCancer:
    date: Optional[datetime.date] = None


@dataclass
class LesionClinical:
    date: Optional[datetime.date] = None
    opinion: Optional[Opinion] = None


@dataclass
class Lesion:
    id: str
    side: Optional[Side] = None
    cyst_aspirated: Optional[bool] = None
    description: Optional[LesionDescription] = None
    position: Optional[LesionPosition] = None
    notes: Optional[str] = None
    # localisation_needed: Optional[bool] = None  # not available
    # localisation_type: Optional[LocalisationType] = None  # not available
    # site_indicator: Optional[SiteIndicator] = None  # not available
    assessment: Optional[LesionAssessment] = None
    clinical: Optional[LesionClinical] = None
    surgery: Optional[LesionSurgery] = None
    biopsy_wide: Optional[LesionBiopsyWide] = None
    biopsy_fine: Optional[LesionBiopsyFine] = None
    interval_cancer: Optional[LesionIntervalCancer] = None

    @property
    def status(self) -> Optional[Status]:
        if self.is_invasive:
            return Status.Invasive
        elif self.is_insitu:
            return Status.Insitu
        else:
            return None

    @property
    def is_invasive(self) -> bool:
        if self.biopsy_wide:
            if self.biopsy_wide.malignant_type == MalignancyType.b:
                return True

            if (
                self.biopsy_wide.invasive_components
                or self.biopsy_wide.invasive_type
                or self.biopsy_wide.disease_grade  # TODO: What if NA?
            ):
                return True

        if self.surgery and (
            self.surgery.invasive_components
            or self.surgery.invasive_type
            or self.surgery.disease_grade
        ):  # TODO: What if NA?
            return True

        return False

    @property
    def is_insitu(self) -> bool:
        if self.is_invasive:
            return False

        if self.biopsy_wide:
            if self.biopsy_wide.malignant_type == MalignancyType.a:
                return True

            # This condition can probably be dropped, but kept for consistency
            if self.biopsy_wide.malignant_type and (
                self.biopsy_wide.malignant_type != MalignancyType.c
            ):
                return False

            if self.biopsy_wide.insitu_components or self.biopsy_wide.dcis_grade:
                return True

        if self.surgery and (self.surgery.insitu_components or self.surgery.dcis_grade):
            return True

        return False

    @property
    def grade(self) -> Optional[Union[HistologicalGrade, DCISGrade]]:
        if self.surgery and self.surgery.disease_grade:
            return self.surgery.disease_grade

        if self.biopsy_wide and self.biopsy_wide.disease_grade:
            return self.biopsy_wide.disease_grade

        if self.surgery and self.surgery.dcis_grade:
            return self.surgery.dcis_grade

        if self.biopsy_wide and self.biopsy_wide.dcis_grade:
            return self.biopsy_wide.dcis_grade

        return None
