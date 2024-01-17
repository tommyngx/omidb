import pytest
import datetime
from omidb import episode, events
from omidb.classificationtools import _earliest_date, _is_time_bounded_ci_prior


def test_normals() -> None:
    episodes = [
        episode.Episode(
            id="1",
            events=events.Events(
                screening=[events.Screening(dates=[datetime.date(2000, 1, 1)])],
                assessment=events.BaseEvent(
                    left_opinion=events.SideOpinion.ON,
                ),
                biopsy_fine=events.BaseEvent(
                    left_opinion=events.SideOpinion.ON,
                ),
            ),
        ),
        episode.Episode(
            id="2",
            events=events.Events(
                screening=[events.Screening(dates=[datetime.date(2000, 2, 1)])],
                assessment=events.BaseEvent(
                    left_opinion=events.SideOpinion.ON,
                ),
            ),
        ),
        episode.Episode(
            id="3",
            events=events.Events(
                screening=[events.Screening(dates=[datetime.date(2000, 3, 1)])],
            ),
        ),
        episode.Episode(  # Null date but treated as valid
            id="4",
            events=events.Events(
                screening=[events.Screening()],
            ),
            opened_date=datetime.date(2000, 4, 1),
        ),
    ]

    expected = [
        episode.Status.NAB,
        episode.Status.NA,
        episode.Status.N,
        episode.Status.N,
    ]
    for ep, exp in zip(episodes, expected):
        assert ep.status == exp


def test_surgery_no_opinion() -> None:
    ep = episode.Episode(
        id="1",
        events=events.Events(
            surgery=events.BaseEvent(left_opinion=events.SideOpinion.ON),
        ),
    )

    assert ep.status is None


def test_invalid_events() -> None:
    ep = episode.Episode(  # Null date but treated as valid
        id="1",
        events=events.Events(clinical=events.BaseEvent()),
        opened_date=datetime.date(2000, 4, 1),
    )

    assert ep.status is None


def test_ci() -> None:
    episodes = [
        episode.Episode(
            id="1",
            type=episode.Type.CI,
        ),
        episode.Episode(
            id="2",
            events=events.Events(
                surgery=events.BaseEvent(left_opinion=events.SideOpinion.ON),
            ),
            type=episode.Type.CI,
        ),
        episode.Episode(
            id="2",
            events=events.Events(
                surgery=events.BaseEvent(left_opinion=events.SideOpinion.OM),
            ),
            type=episode.Type.CI,
        ),
    ]

    expected = [
        episode.Status.CI,
        None,
        episode.Status.CI,
    ]
    for ep, exp in zip(episodes, expected):
        assert ep.status == exp


def test_malignant() -> None:
    episodes = [
        episode.Episode(
            id="1",
            events=events.Events(
                surgery=events.BaseEvent(left_opinion=events.SideOpinion.OM),
            ),
            type=episode.Type.R,
        ),
        episode.Episode(
            id="2",
            events=events.Events(
                biopsy_fine=events.BaseEvent(left_opinion=events.SideOpinion.OM),
            ),
            type=episode.Type.R,
        ),
        episode.Episode(
            id="3",
            events=events.Events(
                biopsy_wide=events.BaseEvent(left_opinion=events.SideOpinion.OM),
            ),
        ),
    ]

    expected = [
        episode.Status.M,
        episode.Status.M,
        episode.Status.M,
    ]
    for ep, exp in zip(episodes, expected):
        assert ep.status == exp


def test_benign() -> None:
    episodes = [
        episode.Episode(
            id="1",
            events=events.Events(
                surgery=events.BaseEvent(left_opinion=events.SideOpinion.OB),
            ),
            type=episode.Type.R,
        ),
        episode.Episode(
            id="2",
            events=events.Events(
                biopsy_fine=events.BaseEvent(left_opinion=events.SideOpinion.OB),
            ),
            type=episode.Type.R,
        ),
        episode.Episode(
            id="3",
            events=events.Events(
                biopsy_wide=events.BaseEvent(left_opinion=events.SideOpinion.OB),
            ),
        ),
    ]

    expected = [
        episode.Status.B,
        episode.Status.B,
        episode.Status.B,
    ]
    for ep, exp in zip(episodes, expected):
        assert ep.status == exp
