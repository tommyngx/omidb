from dataclasses import dataclass, field
from typing import Optional, Set
import enum


@enum.unique
class BenignClassification(enum.Enum):
    """Description of the benign feature"""

    coarse = "coarse_or_popcorn-like"
    egg_shell = "egg_shell_or_rim"
    lucent_centred = "lucent-centred"
    rod = "rod-like"
    round_puncate = "round_and_punctate"


@enum.unique
class Conspicuity(enum.Enum):
    """Indicates this marks conspicuity"""

    obvious = "Obvious"
    subtle = "Subtle"
    very_subtle = "Very_subtle"
    occult = "Occult"
    not_recalled = "not_recalled"


@enum.unique
class MassClassification(enum.Enum):
    """Description of the mass border"""

    ill_defined = "ill_defined"
    spiculated = "spiculated"
    well_defined = "well_defined"
    other = "other"
    unknown = "unknown"
    lucent_centred = "lucent-centred"
    course = "coarse_or_popcorn-like"
    egg_shell = "egg_shell_or_rim"


@dataclass
class BoundingBox:
    """2D coordinates defining the mark"""

    x1: int
    y1: int
    x2: int
    y2: int


@dataclass
class Mark:
    """
    A ground-truth region of interest made by an expert radiologist. A mark
    includes the region of interest and descriptions characterising the
    lesion.

    Note that boolean attributes default to ``None``, rather than ``False``, to
    reduce misinterpretation when the source attribute has not been set by the
    Radiologist. Interpret as 'no value'.

    :param id: An identifier for the annotation
    :param boundingBox: 2D coordinates defining the lower-left (x1, y1) and
        upper-right (x2, y2) corners of the mark
    :param conspicuity: Enumeration indicating mark conspicuity
    :param lesion_ids: An set of identifiers for the lesions associated with
        this mark; unique within episode only. Corresponds to the
        `LinkedNBSSLesionNumber` field of the ImageDB JSON, which itself
        maps to the key of the lesion referenced by the NBSS JSON.
    :param architectural_distortion: The mark highlights architectural
        distortion
    :param dystrophic_calcification: The mark highlights dystrophic
        calcification
    :param fat_necrosis: The mark highlights an area of fat necrosis
    :param focal_asymmetry: Indicates focal asymmetry
    :param mass: The marked lesion is a mass
    :param suspicious_calcifications: Indicates a suspicious calcification
        cluster
    :param milk_of_calcium: The mark highlights milk of calcium mammographic
        features
    :param other_benign_cluster: The mark surrounds a benign calcification
        cluster not described by other parameters
    :param plasma_cell_mastitis: The marked area indicates plasma-cell-mastitis
    :param benign_skin_feature: The mark captures a benign skin lesion,
        calcified or other
    :param calcifications: The marked area has calcifications
    :param suture_calcification: The marked area indicates suture
        calcifications
    :param vascular_feature: The marked area indicates vascular calcifications
    :param benign_classification: Enumeration describing the benign feature
    :param mass_classification: Enumeration describing the mass border
    """

    id: str
    boundingBox: BoundingBox
    conspicuity: Conspicuity
    lesion_ids: Set[str] = field(default_factory=set)
    architectural_distortion: Optional[bool] = None
    dystrophic_calcification: Optional[bool] = None
    fat_necrosis: Optional[bool] = None
    focal_asymmetry: Optional[bool] = None
    mass: Optional[bool] = None
    suspicious_calcifications: Optional[bool] = None
    milk_of_calcium: Optional[bool] = None
    other_benign_cluster: Optional[bool] = None
    plasma_cell_mastitis: Optional[bool] = None
    benign_skin_feature: Optional[bool] = None
    calcifications: Optional[bool] = None
    suture_calcification: Optional[bool] = None
    vascular_feature: Optional[bool] = None
    benign_classification: Optional[BenignClassification] = None
    mass_classification: Optional[MassClassification] = None
