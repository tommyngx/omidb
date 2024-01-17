import omidb
from omidb import client_parser as cp

"""
Artificial data for testing purposes (assume properties have no relation)
"""

episode_data = {
    "LESION": {
        "R": {
            "1": {
                "CystAspirated": "N",
                "LesionDescription": "Mass with calcification",
                "LesionNotes": None,
                "LesionPosition": "RB3",
            }
        }
    },
    "BIOPSYWIDE": {
        "Opinion": None,
        "R": {
            "1": {
                "BenignLesions": None,
                "CalcificationOnSpecimen": None,
                "DatePerformed": "1950-02-22",
                "DcisGrade": "NDI",
                "DiagnosticSetOutcome": "W+",
                "DiseaseGrade": "G3",
                "EpithelialProliferation": None,
                "HER2ReceptorScore": None,
                "HER2ReceptorStatus": None,
                "HistologicalCalcification": "A",
                "HormoneERScore": None,
                "HormoneERStatus": None,
                "HormonePRScore": None,
                "HormonePRStatus": None,
                "InSituComponents": "NID",
                "InsituPresent": None,
                "InvasiveComponents": "IDC",
                "InvasivePresent": "Y",
                "InvasiveType": "IN",
                "InvasiveTypeOther": None,
                "LocalisationType": "U",
                "Location": None,
                "LymphNode": "N",
                "MalignancyType": "b",
                "NeedleSpecimenType": "WBN",
                "Opinion": "B5",
                "SideCode": "R",
                "SpecimenType": None,
                "left_opinion": "Normal",
                "right_opinion": "Malignant",
            }
        },
        "dateperformed": "1950-02-22",
        "diagnosticsetoutcome": "W+",
        "left_opinion": None,
        "right_opinion": "Malignant",
    },
    "SURGERY": {
        "Opinion": None,
        "R": {
            "1": {
                "AxillaryMetsType": "MET",
                "AxillaryNodesNumberPositive": "1",
                "AxillaryNodesPositive": None,
                "AxillarySpecimenType": None,
                "BenignLesions": None,
                "BiopsySpecimenType": "WX",
                "CalcificationsOnSpecimen": None,
                "CancerOnKC62": "N",
                "Chemotherapy": None,
                "DatePerformed": "1950-05-13",
                "DcisGrade": "NDI",
                "DcisGrowthPatterns": "GC GP",
                "DiagnosticProcedure": None,
                "DiseaseExtent": "DEL",
                "DiseaseGrade": "G3",
                "EpithelialProliferation": None,
                "Event": "PTR",
                "ExcisionMarginDistance": "2.0",
                "ExcisionMargins": "ED",
                "HER2ReceptorScore": "1+",
                "HER2ReceptorStatus": "RN",
                "HistologicalCalcification": "A",
                "HormoneERScore": "8",
                "HormoneERStatus": "RP",
                "HormonePRScore": "8",
                "HormonePRStatus": "RP",
                "InSituComponents": "NID",
                "InvasiveComponents": "IDC",
                "InvasiveType": "IN",
                "InvasiveTypeOther": None,
                "LocalTrialCode": None,
                "Microinvasion": "MNP",
                "NationalTrial": None,
                "NonsurgicalTreatments": None,
                "Opinion": "H5",
                "ReconstructiveProcedure": "NO",
                "SizeDuctalOnly": None,
                "TherapeuticProcedures": "SD AC",
                "TreatmentProcedure": "WLE",
                "WholeSizeOfTumour": "16.0",
                "left_opinion": "Normal",
                "right_opinion": "Malignant",
            }
        },
        "dateperformed": "1950-05-13",
        "diagnosticsetoutcome": "H+",
        "left_opinion": None,
        "right_opinion": "Malignant",
    },
}


def test_parse_lesion() -> None:

    parser = cp.ClientParser("", {}, {}, [], False)
    parsed_lesions = parser._parse_lesions(episode_data)

    for side, side_data in episode_data["LESION"].items():
        for id, lesion_data in side_data.items():
            lesion = parsed_lesions[id]
            assert lesion.id == id
            assert lesion.side.name == side
            assert lesion.description.value == lesion_data["LesionDescription"]
            assert lesion.position.name == lesion_data["LesionPosition"]


def test_parse_biopsy_wide_lesion() -> None:

    parser = cp.ClientParser("", {}, {}, [], False)

    for side, side_data in episode_data["LESION"].items():
        for id, _ in side_data.items():

            lesion_event = parser._parse_biopsy_wide_lesion(
                episode_data, side, id)
            event_data = episode_data["BIOPSYWIDE"][side][id]
            assert str(lesion_event.date) == event_data["DatePerformed"]
            assert str(
                lesion_event.disease_grade.name) == event_data["DiseaseGrade"]
            assert (
                str(lesion_event.invasive_components[0].name)
                == event_data["InvasiveComponents"]
            )
            assert str(
                lesion_event.invasive_type.name) == event_data["InvasiveType"]
            assert (
                str(lesion_event.insitu_components[0].name)
                == event_data["InSituComponents"]
            )
            assert str(lesion_event.dcis_grade.name) == event_data["DcisGrade"]
            assert str(
                lesion_event.malignant_type.name) == event_data["MalignancyType"]
            assert lesion_event.opinion.name == event_data.get("Opinion")


def test_parse_surgery_lesion() -> None:

    parser = cp.ClientParser("", {}, {}, [], False)

    for side, side_data in episode_data["LESION"].items():
        for id, _ in side_data.items():

            lesion_event = parser._parse_surgery_lesion(episode_data, side, id)

            event_data = episode_data["SURGERY"][side][id]
            assert str(lesion_event.date) == event_data["DatePerformed"]
            assert str(
                lesion_event.disease_grade.name) == event_data["DiseaseGrade"]
            assert (
                str(lesion_event.invasive_components[0].name)
                == event_data["InvasiveComponents"]
            )
            assert str(
                lesion_event.invasive_type.name) == event_data["InvasiveType"]
            assert (
                str(lesion_event.insitu_components[0].name)
                == event_data["InSituComponents"]
            )
            assert str(lesion_event.dcis_grade.name) == event_data["DcisGrade"]
            assert lesion_event.opinion.name == event_data.get("Opinion")
