import datetime
import pathlib
import omidb
from omidb.classificationtools import _earliest_date
from typing import Any


def get_client() -> omidb.client.Client:

    mark = omidb.mark.Mark(
        "1", "2", (omidb.mark.BoundingBox(0, 0, 0, 0)
                   ), omidb.mark.Conspicuity.subtle
    )

    image = omidb.image.Image("1.2.3", pathlib.Path(), pathlib.Path(), [mark])

    # Make up some attributes for this dicom
    image._json = {
        "00080070": {"Value": ["HOLOGIC, Inc."]},
        "00081090": {"Value": ["New Model"]},
        "00080068": {"Value": ["FOR PROCESSING"]},
        "00200062": {"Value": ["L"]},
        "00185101": {"Value": ["CC"]},
        "00540220": {
            "Value": [
                {
                    "00080100": {"Value": ["R-10242"]},
                    "00080104": {"Value": ["cranio-caudal"]},
                }
            ],
        },
        "001811A0": {"Value": [50]},
        "00101010": {"Value": ["065Y"]},
        "00020010": {"Value": ["1.2.840.10008.1.2"]},
    }

    series = omidb.series.Series("1.2.3.4", [image])

    study = omidb.study.Study(
        "1.2.3.4.5",
        series=[series],
        event_type=[omidb.events.Event.screening, omidb.events.Event.clinical],
        date=datetime.date(2014, 6, 12),
    )

    events = omidb.events.Events(
        screening=[omidb.events.Screening(dates=[datetime.date(2000, 2, 1)])],
        clinical=omidb.events.BaseEvent(
            left_opinion=omidb.events.SideOpinion.ON),
    )

    episode = omidb.episode.Episode(
        "1.2.3.4.5.6",
        studies=[study],
        events=events,
        type=omidb.episode.Type.F,
        action=omidb.episode.Action.EC,
        opened_date=datetime.date(2014, 6, 12),
        closed_date=datetime.date(2014, 8, 12),
    )

    client = omidb.client.Client("abc1", [episode], "site")

    return client


def test_write_client_data() -> None:

    client = get_client()
    writer = omidb.commands.summarise.write_client_data([client])

    expected: Any = None
    # type: ignore
    for k, v, v2 in zip(writer.rows[0], writer.rows[1], writer.rows[2]):
        if k == "ClientID":
            expected = client.id
        elif k == "ClientStatus":
            expected = client.status.name
        elif k == "Site":
            expected = client.site
        elif k == "EpisodeID":
            expected = client.episodes[0].id
        elif k == "EpisodeSortDate":
            expected = _earliest_date(client.episodes[0])
        elif k == "EpisodeType":
            expected = client.episodes[0].type.name
        elif k == "EpisodeStatus":
            expected = omidb.episode.Status.N.name
        elif k == "EpisodeOutcome":
            expected = "N"
        elif k == "EpisodeOutcomeFutureEpisodeID":
            expected = None
        elif k == "EpisodeIsPostOp":
            expected = False
        elif k == "EpisodeAction":
            expected = client.episodes[0].action.name
        elif k == "EpisodeContainsMalignantOpinions":
            expected = client.episodes[0].has_malignant_opinions
        elif k == "EpisodeContainsBenignOpinions":
            expected = client.episodes[0].has_benign_opinions
        elif k == "EpisodeOpenedDate":
            expected = client.episodes[0].opened_date
        elif k == "EpisodeClosedDate":
            expected = client.episodes[0].closed_date
        elif k == "ActualEpisodeOpenedYear":
            expected = client.episodes[0].actual_opened_year
        elif k == "EpisodeHasEvents":
            expected = client.episodes[0].events is not None
        elif k == "StudyInstanceUID":
            expected = client.episodes[0].studies[0].id
        elif k == "StudyDate":
            expected = client.episodes[0].studies[0].date
        elif k == "EventType":
            # type: ignore
            expected = client.episodes[0].studies[0].event_type[0].name
            assert v == expected
            # type: ignore
            expected = client.episodes[0].studies[0].event_type[1].name
            assert v2 == expected
            continue
        elif k == "SeriesInstanceUID":
            expected = client.episodes[0].studies[0].series[0].id
        elif k == "SeriesInstanceUID":
            expected = client.episodes[0].studies[0].series[0].id
        elif k == "SOPInstanceUID":
            expected = client.episodes[0].studies[0].series[0].images[0].id
        elif k == "NumberOfMarks":
            expected = len(
                # type: ignore
                client.episodes[0].studies[0].series[0].images[0].marks
            )
        else:
            # type: ignore
            image = client.episodes[0].studies[0].series[0].images[0]
            if k == "Manufacturer":
                # type: ignore
                expected = image.attributes["00080070"]["Value"][0]
            elif k == "Model":
                # type: ignore
                expected = image.attributes["00081090"]["Value"][0]
            elif k == "BodyPartThicknessMM":
                # type: ignore
                expected = image.attributes["001811A0"]["Value"][0]
            elif k == "PatientAgeYears":
                expected = 65
            elif k == "PresentationIntentType":
                # type: ignore
                expected = image.attributes["00080068"]["Value"][0]
            elif k == "ImageLaterality":
                # type: ignore
                expected = image.attributes["00200062"]["Value"][0]
            elif k == "ViewPosition":
                # type: ignore
                expected = image.attributes["00185101"]["Value"][0]
            elif k == "ViewModCodeValue":
                expected = image.attributes["00540220"]["Value"][0]["00080100"][
                    "Value"
                ][
                    0
                ]  # type: ignore
            elif k == "ViewModCodeMeaning":
                expected = image.attributes["00540220"]["Value"][0]["00080104"][
                    "Value"
                ][
                    0
                ]  # type: ignore
            elif k == "TransferSyntaxUID":
                # type: ignore
                expected = image.attributes["00020010"]["Value"][0]
            else:
                raise ValueError(f"{k} unknown")

        assert (v == expected) & (v2 == expected)
