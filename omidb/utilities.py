import enum
import datetime
import re
from typing import Optional, Union, Dict, Any, List
from .image import Image
import json
from loguru import logger

IUID_REG = re.compile(r"[\d+.]+$")


def str_to_date(date: str) -> datetime.date:
    if "-" in date:
        return datetime.datetime.strptime(date, "%Y-%m-%d").date()
    else:
        return datetime.datetime.strptime(date, "%Y%m%d").date()


def date_or_none(d: Dict[Any, Any], key: Any) -> Optional[datetime.date]:
    if d.get(key):
        return str_to_date(d[key])
    return None


def enum_lookup(
    value: str, e: enum.EnumMeta, should_raise: bool = False
) -> Optional[Any]:
    if value is None or value == "":
        return None
    for mem in e:  # type: ignore
        if value == mem.name or value == mem.value:  # type: ignore
            return mem
    logger.warning(f"`{value}` was not found in enum `{e}`")
    if should_raise:
        raise ValueError(f"`{value}` was not found in enum `{e}`")
    return None


def try_image_attribute(
    attributes: Union[Dict[str, Any], Image], tags: Union[str, List[str]]
) -> Optional[Any]:
    if isinstance(tags, str):
        tags = [tags]

    try:
        if isinstance(attributes, Image):
            attrs = attributes.attributes
        else:
            attrs = attributes
        for t in tags:
            attrs = attrs[t]["Value"][0]  # type: ignore
        return attrs
    except (KeyError, json.decoder.JSONDecodeError):
        pass
    return None


def parse_age(image: Image) -> Optional[int]:
    try:
        age_s = try_image_attribute(image, "00101010")
    except AttributeError:
        return None
    if not isinstance(age_s, str):
        return None
    match = re.match(r"\d+", age_s.lstrip("0"))
    if match is None:
        return None
    age = int(match.group())
    if age_s.endswith("M"):
        age = age // 12
    if age_s.endswith("W"):
        age = age // 52
    if age_s.endswith("D"):
        age = age // 365
    return age


# TODO: Replace these with enums
ListProperties = {
    " ": (
        "ReferralReasons",
        "IntervalCancerReviewers",
        "IntervalCancerReviewersN",
        "AdditionalBiopsyProcs",
        "AdditionalTreatmentProcs",
        "BenignLesions",
        "EpithelialProliferation",
        "Invasive",
        "NonInvasive",
        "RadiotherapySites",
        "NewTreatments",
        "Clinicians",
        "CliniciansNational",
        "MammoAttributes",
        "MammoClinicians",
        "MammoCliniciansNat",
        "UssAttributes",
        "UssClinicians",
        "UssCliniciansNat",
        "Attendees",
        "AttendeesNational",
        "OutcomeSubcategory",
        "Readers",
        "RecommendedActions",
        "FilmReaders",
        "FilmRecommendedActions",
        "Appearance",
        "Margin",
        "ViewsProcedures",
        "AdditionalDiagnosticProcs",
        "AdditionalTreatmentProcs",
        "AxillarySpecimenTypes",
        "BenignLesions",
        "DcisGrowthPatterns",
        "DiseaseExtent",
        "EpithelialProliferation",
        "InSituComponents",
        "InvasiveComponents",
        "NonsurgicalTreatments",
        "InSituComponents",
        "UncertainLesions",
    ),
    ",": (
        "SpecialAppointmentReasons",
        "OtherGeneCodes",
        "EpisodeEndPoint",
        "ReadersNational",
        "FilmReadersNational",
    ),
}


# TODO: Drop the need for `key`
def nbss_str_to_enum(
    value: Any, e: enum.EnumMeta, key: Optional[str] = None
) -> Optional[Any]:
    if value in (None, ""):
        return None

    # Check if property is 'list like' and attempt to parse as list of enums
    if key is not None:
        for sep, props in ListProperties.items():
            if key in props:
                result = []
                for v in value.split(sep):
                    t = enum_lookup(v, e)
                    if t is not None:
                        result.append(t)
                return result

    # Single value, so return enum
    return enum_lookup(value, e)
