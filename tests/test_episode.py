import pytest
import datetime
from omidb import episode, events
from omidb.classificationtools import _earliest_date, _is_time_bounded_ci_prior


def test_earliest_date_event_date_over_episode_opened() -> None:
    expected = datetime.date(2000, 1, 1)
    ep = episode.Episode(
        id="1",
        events=events.Events(screening=[events.Screening(dates=[expected])]),
        opened_date=expected - datetime.timedelta(days=1),
    )
    assert _earliest_date(ep) == expected


def test_earliest_date_episode_opened_no_events() -> None:
    expected = datetime.date(2000, 1, 1)
    ep = episode.Episode(
        id="1",
        events=events.Events(screening=[events.Screening()]),
        opened_date=expected,
    )
    assert _earliest_date(ep) == expected


def test_earliest_date_interval_cancer() -> None:
    expected = datetime.date(2000, 1, 1)
    ep = episode.Episode(
        id="1",
        events=events.Events(screening=[events.Screening()]),
        opened_date=expected - datetime.timedelta(days=1),  # ignored!
        diagnosis_date=expected,
        type=episode.Type.CI,
    )
    assert _earliest_date(ep) == expected


def test_earliest_date_multiple_screens() -> None:
    expected = datetime.date(2000, 1, 1)
    ep = episode.Episode(
        id="1",
        events=events.Events(
            screening=[events.Screening(dates=[expected, datetime.date(2000, 2, 1)])],
        ),
    )
    assert _earliest_date(ep) == expected


def test_earliest_date_multiple_events() -> None:
    expected = datetime.date(2000, 1, 1)
    ep = episode.Episode(
        id="1",
        events=events.Events(
            screening=[events.Screening(dates=[expected + datetime.timedelta(days=1)])],
            surgery=events.BaseEvent(dates=[expected]),
        ),
    )
    assert _earliest_date(ep) == expected


def test_earliest_date_episode_raises_when_no_dates() -> None:
    ep = episode.Episode(
        id="1",
        events=events.Events(screening=[events.Screening()]),
    )
    with pytest.raises(ValueError):
        _earliest_date(ep)


def test_earliest_date_episode_raises_when_ci_has_only_opened_date() -> None:
    ep = episode.Episode(
        id="1",
        events=events.Events(screening=[events.Screening()]),
        opened_date=datetime.date(2000, 1, 1),
        type=episode.Type.CI,
    )
    with pytest.raises(ValueError):
        _earliest_date(ep)
