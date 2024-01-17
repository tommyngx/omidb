import pytest
import datetime
from typing import Optional, Union
from omidb import episode, events
from omidb.classificationtools import (
    episode_outcome,
    is_post_op,
    _within_time_period,
    _is_time_bounded_ci_prior,
    _is_time_bounded_cancer_prior,
    _find_next_episode,
    EpisodeOutcome,
    UndefinedEpisodeOutcome,
)


def test_find_next_episode() -> None:
    episodes = [
        episode.Episode(
            id="1",
            events=events.Events(
                screening=[events.Screening(dates=[datetime.date(2000, 2, 1)])]
            ),
        ),
        episode.Episode(
            id="2",
            events=events.Events(
                screening=[events.Screening(dates=[datetime.date(2000, 1, 1)])]
            ),
        ),
    ]

    next_epsiode = _find_next_episode(episodes[0], episodes)
    assert next_epsiode is None
    next_epsiode = _find_next_episode(episodes[1], episodes)
    assert next_epsiode == episodes[0]


@pytest.mark.parametrize("threshold, expected", [(2, True), (1, False)])
def test_within_time_period(threshold: int, expected: bool) -> None:
    e1 = episode.Episode(
        id="1",
        events=events.Events(
            screening=[events.Screening(dates=[datetime.date(2000, 1, 1)])]
        ),
    )
    e2 = episode.Episode(
        id="2",
        events=events.Events(
            screening=[events.Screening(dates=[datetime.date(2000, 3, 1)])]
        ),
    )
    assert _within_time_period(e1, e2, threshold) == expected


@pytest.mark.parametrize(
    "opinion, expected", [(events.SideOpinion.OM, True),
                          (events.SideOpinion.OS, None)]
)
def test_is_time_bounded_ci_prior(opinion: events.SideOpinion, expected: bool) -> None:
    e1 = episode.Episode(
        id="1",
        events=events.Events(
            screening=[events.Screening(dates=[datetime.date(2000, 1, 1)])]
        ),
    )
    e2 = episode.Episode(
        id="2",
        events=events.Events(
            surgery=events.BaseEvent(
                dates=[datetime.date(2000, 3, 1)], left_opinion=opinion
            )
        ),
        type=episode.Type.CI,
    )

    assert _is_time_bounded_ci_prior(e1, e2) == expected


@pytest.mark.parametrize(
    "opinion, expected", [(events.SideOpinion.OM, True),
                          (events.SideOpinion.OS, False)]
)
def test_is_time_bounded_cancer_prior(
    opinion: events.SideOpinion, expected: bool
) -> None:
    e1 = episode.Episode(
        id="1",
        events=events.Events(
            screening=[events.Screening(dates=[datetime.date(2000, 1, 1)])]
        ),
    )
    e2 = episode.Episode(
        id="2",
        events=events.Events(
            surgery=events.BaseEvent(
                dates=[datetime.date(2000, 3, 1)], left_opinion=opinion
            )
        ),
    )

    assert _is_time_bounded_cancer_prior(e1, e2) == expected


@pytest.mark.parametrize("days_offset, expected", [(-1, False), (0, False), (1, True)])
def test_is_post_op(days_offset: int, expected: bool) -> None:
    surgery_date = datetime.date(2000, 2, 1)
    screening_date = surgery_date + datetime.timedelta(days=days_offset)
    episodes = [
        episode.Episode(
            id="1",
            events=events.Events(
                screening=[events.Screening(dates=[screening_date])]),
        ),
        episode.Episode(
            id="2",
            events=events.Events(
                surgery=events.BaseEvent(
                    dates=[surgery_date], left_opinion=events.SideOpinion.OM
                )
            ),
        ),
    ]

    assert is_post_op(episodes[0], episodes) == expected


@pytest.mark.parametrize(
    "ep_type, opinion, expected",
    [
        (episode.Type.CI, events.SideOpinion.OM, True),
        (episode.Type.CI, events.SideOpinion.OS, False),
        (episode.Type.F, events.SideOpinion.OM, False),
    ],
)
def test_is_interval_cancer_surgery_opinion(
    ep_type: episode.Type, opinion: events.SideOpinion, expected: bool
) -> None:
    e = episode.Episode(
        id="1",
        events=events.Events(
            surgery=events.BaseEvent(
                dates=[datetime.date(2000, 3, 1)], left_opinion=opinion
            )
        ),
        type=ep_type,
    )

    assert e.is_interval_cancer == expected


def test_is_interval_cancer_no_events_no_dates() -> None:
    e = episode.Episode(id="1", events=None, type=episode.Type.CI)
    assert e.is_interval_cancer


def test_classify_no_events() -> None:
    e = episode.Episode(id="1", events=None, type=episode.Type.R)
    assert episode_outcome(e, [e])[0] == UndefinedEpisodeOutcome.InvalidEvents


def test_classify_no_dates() -> None:
    e = episode.Episode(
        id="1",
        events=events.Events(
            screening=events.BaseEvent(
                dates=None,
                left_opinion=events.SideOpinion.ON,
            )
        ),
        type=episode.Type.R,
        opened_date=None,
    )
    assert episode_outcome(e, [e])[0] == UndefinedEpisodeOutcome.DateError


def test_classify_next_episode_no_events() -> None:

    episodes = [
        episode.Episode(
            id="1",
            type=episode.Type.F,
            events=events.Events(
                screening=events.BaseEvent(
                    dates=[datetime.date(2000, 3, 1)],
                    left_opinion=events.SideOpinion.ON,
                )
            ),
        ),
        episode.Episode(
            id="2",
            type=episode.Type.R,
            events=None,
            opened_date=datetime.date(2000, 4, 1),
        ),
    ]

    expected = [
        UndefinedEpisodeOutcome.InvalidEvents,
        UndefinedEpisodeOutcome.InvalidEvents
    ]
    for ep, exp in zip(episodes, expected):
        assert episode_outcome(
            ep, episodes, num_months_normal_follow_up=0)[0] == exp


def test_classify_null_events() -> None:
    episodes = [
        episode.Episode(
            id="1",
            events=events.Events(
                screening=[events.Screening()],
                assessment=events.BaseEvent(
                    left_opinion=events.SideOpinion.ON),
                biopsy_fine=events.BaseEvent(
                    left_opinion=events.SideOpinion.ON),
            ),
            opened_date=datetime.date(2000, 1, 1),
        ),
        episode.Episode(  # This is the problematic episode
            id="2",
            events=events.Events(
                screening=[events.Screening()],
                assessment=events.BaseEvent(),
            ),
            opened_date=datetime.date(2000, 2, 1),
        ),
    ]

    assert (
        episode_outcome(episodes[0], episodes)[0]
        == UndefinedEpisodeOutcome.InvalidEvents
    )
    assert (
        episode_outcome(episodes[1], episodes)[0]
        == UndefinedEpisodeOutcome.InvalidEvents
    )


def test_classify_null_events_with_time_threshold() -> None:
    episodes = [
        episode.Episode(
            id="1",
            events=events.Events(
                screening=[events.Screening()],
                assessment=events.BaseEvent(
                    left_opinion=events.SideOpinion.ON),
                biopsy_fine=events.BaseEvent(
                    left_opinion=events.SideOpinion.ON),
            ),
            opened_date=datetime.date(2000, 1, 1),
        ),
        episode.Episode(  # This is fine
            id="2",
            events=events.Events(
                screening=[events.Screening()],
            ),
            opened_date=datetime.date(2000, 2, 1),
        ),
        episode.Episode(  # Problematic episode within the time window
            id="3",
            events=events.Events(
                screening=[events.Screening()],
                assessment=events.BaseEvent(),
            ),
            opened_date=datetime.date(2000, 3, 1),
        ),
    ]

    assert (
        episode_outcome(episodes[0], episodes, 10, 10)[0]
        == UndefinedEpisodeOutcome.InvalidEvents
    )


def test_classify_normals() -> None:

    episodes = [
        episode.Episode(
            id="1",
            events=events.Events(
                screening=[events.Screening(
                    dates=[datetime.date(2000, 1, 1)])],
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
                screening=[events.Screening(
                    dates=[datetime.date(2000, 2, 1)])],
                assessment=events.BaseEvent(
                    left_opinion=events.SideOpinion.ON,
                ),
            ),
        ),
        episode.Episode(
            id="3",
            events=events.Events(
                screening=[events.Screening(
                    dates=[datetime.date(2000, 3, 1)])],
            ),
        ),
        episode.Episode(  # Null date but treated as valid
            id="4",
            events=events.Events(
                screening=[events.Screening()],
            ),
            opened_date=datetime.date(2000, 4, 1),
        ),
        episode.Episode(
            id="5",
            events=events.Events(
                screening=[events.Screening(
                    dates=[datetime.date(2000, 4, 2)])],
            ),
        ),
    ]

    expected = [
        EpisodeOutcome.NAB,
        EpisodeOutcome.NA,
        EpisodeOutcome.N,
        EpisodeOutcome.N,
        UndefinedEpisodeOutcome.NoSubsequentEpisode,
    ]
    for ep, exp in zip(episodes, expected):
        assert episode_outcome(
            ep,
            episodes,
            num_months_normal_follow_up=0,
        )[0] == exp


def test_classify_cancers() -> None:

    episodes = [
        episode.Episode(
            id="1",
            events=events.Events(
                surgery=events.BaseEvent(
                    dates=[datetime.date(2000, 3, 1)],
                    left_opinion=events.SideOpinion.OM,
                )
            ),
        ),
        episode.Episode(
            id="2",
            type=episode.Type.CI,
            events=events.Events(
                surgery=events.BaseEvent(
                    dates=[datetime.date(2000, 3, 1)],
                    left_opinion=events.SideOpinion.OM,
                )
            ),
        ),
    ]

    expected = [
        EpisodeOutcome.M,
        EpisodeOutcome.CI,
    ]
    for ep, exp in zip(episodes, expected):
        assert episode_outcome(ep, episodes)[0] == exp


def test_ci_prior_no_events() -> None:
    date = datetime.date(2000, 1, 1)
    date2 = date + datetime.timedelta(days=1)

    episodes = [
        episode.Episode(
            id="1",
            events=events.Events(
                screening=[events.Screening(dates=[date])],
            ),
        ),
        episode.Episode(
            id="2", events=None, type=episode.Type.CI, diagnosis_date=date2
        ),
    ]

    assert episode_outcome(episodes[0], episodes)[0] == EpisodeOutcome.CIP
    assert episode_outcome(episodes[1], episodes)[0] == EpisodeOutcome.CI


@pytest.mark.parametrize(
    "ep_type, expected",
    [
        (episode.Type.R, EpisodeOutcome.MP),
        (episode.Type.CI, EpisodeOutcome.CIP),
    ],
)
def test_cancer_prior_default_thresholds(
    ep_type: episode.Type, expected: EpisodeOutcome
) -> None:

    date = datetime.date(2000, 1, 1)
    date2 = date + datetime.timedelta(days=10 * 365 / 12)
    date3 = date + datetime.timedelta(days=100 * 365 / 12)

    episodes = [
        episode.Episode(
            id="1",
            events=events.Events(
                screening=[events.Screening(dates=[date])],
            ),
        ),
        episode.Episode(
            id="2",
            events=events.Events(
                screening=[events.Screening(dates=[date])],
            ),
        ),
        episode.Episode(
            id="3",
            events=events.Events(
                surgery=events.BaseEvent(
                    dates=[date2], left_opinion=events.SideOpinion.OM
                )
            ),
            type=ep_type,
        ),
    ]

    assert episode_outcome(episodes[0], episodes)[0] == EpisodeOutcome.N
    assert episode_outcome(episodes[1], episodes)[0] == expected


@pytest.mark.parametrize(
    "month_offset, ep_type, expected",
    [
        (39, episode.Type.R, EpisodeOutcome.MP),
        (40, episode.Type.R, EpisodeOutcome.N),
        (36, episode.Type.CI, EpisodeOutcome.CIP),
        (37, episode.Type.CI, UndefinedEpisodeOutcome.InvalidPrior),
    ],
)
def test_cancer_prior_with_months(
    month_offset: int, ep_type: episode.Type, expected: Optional[EpisodeOutcome]
) -> None:

    date = datetime.date(2000, 1, 1)
    date2 = date + datetime.timedelta(days=(month_offset - 1) * 365 / 12)
    date3 = date + datetime.timedelta(days=month_offset * 365 / 12)

    episodes = [
        episode.Episode(
            id="1",
            events=events.Events(
                screening=[events.Screening(dates=[date])],
            ),
        ),
        episode.Episode(
            id="2",
            events=events.Events(
                screening=[events.Screening(dates=[date2])],
            ),
        ),
        episode.Episode(
            id="3",
            events=events.Events(
                surgery=events.BaseEvent(
                    dates=[date3], left_opinion=events.SideOpinion.OM
                )
            ),
            type=ep_type,
        ),
    ]

    got = episode_outcome(
        episodes[0], episodes, num_months_ci_prior=36, num_months_cancer_prior=39
    )[0]
    assert got == expected


@pytest.mark.parametrize(
    "cancer_interval, cancer_month_offset, normal_month_offset, expected",
    [
        (20, 21, 31, UndefinedEpisodeOutcome.InvalidPrior),
        (20, 32, 31, EpisodeOutcome.N),
        (None, 1, 31, EpisodeOutcome.MP),
        (None, 32, 31, EpisodeOutcome.N),
        (None, 32, 30, UndefinedEpisodeOutcome.InvalidPrior),
    ],
)
def test_normals_follow_up_and_cancer_prior_rules(
    cancer_interval: Optional[int],
    cancer_month_offset: int,
    normal_month_offset: int,
    expected: Optional[EpisodeOutcome],
) -> None:

    date = datetime.date(2000, 1, 1)
    # not an MP as too late
    date2 = date + datetime.timedelta(days=cancer_month_offset * 365 / 12)
    # satisfies normal follow up requirement
    date3 = date + datetime.timedelta(days=normal_month_offset * 365 / 12)

    episodes = [
        episode.Episode(
            id="1",
            events=events.Events(
                screening=[events.Screening(dates=[date])],
            ),
        ),
        episode.Episode(
            id="2",
            events=events.Events(
                surgery=events.BaseEvent(
                    dates=[date2], left_opinion=events.SideOpinion.OM
                )
            ),
        ),
        episode.Episode(
            id="3",
            events=events.Events(
                screening=[events.Screening(dates=[date3])],
            ),
        ),
    ]
    got = episode_outcome(
        episodes[0],
        episodes,
        num_months_cancer_prior=cancer_interval,
        num_months_normal_follow_up=30,
    )[0]
    assert got == expected


@pytest.mark.parametrize(
    "offset1, offset2, benign_follow_up_months, expected",
    [
        (39, 80, None, EpisodeOutcome.MP),
        (40, 80, None, EpisodeOutcome.B),
        (40, 80, 1, UndefinedEpisodeOutcome.InvalidPrior),
        (45, 80, 60, UndefinedEpisodeOutcome.InvalidPrior),
        (-1, -1, None, EpisodeOutcome.B),  # no follow-up
        (-1, 2, 1, EpisodeOutcome.B),  # normal follow up
        # normal follow up too early
        (-1, 2, 3, UndefinedEpisodeOutcome.InvalidFollowUp),
        # follow up too early, cancer too later
        (80, 2, 3, UndefinedEpisodeOutcome.InvalidPrior),
    ],
)
def test_benign(
    offset1: int,
    offset2: int,
    benign_follow_up_months: Optional[int],
    expected: Union[EpisodeOutcome, UndefinedEpisodeOutcome],
) -> None:

    date = datetime.date(2000, 1, 1)
    date2 = date + datetime.timedelta(days=offset1 * 365 / 12)
    date3 = date + datetime.timedelta(days=offset2 * 365 / 12)

    episodes = [
        episode.Episode(
            id="1",
            events=events.Events(
                biopsy_wide=events.BaseEvent(
                    dates=[date], left_opinion=events.SideOpinion.OB),
            ),
        ),
        episode.Episode(
            id="2",
            events=events.Events(
                surgery=events.BaseEvent(
                    dates=[date2], left_opinion=events.SideOpinion.OM
                )
            ),
        ),
        episode.Episode(
            id="3",
            events=events.Events(
                screening=[events.Screening(dates=[date3])],
            ),
        ),
    ]
    got = episode_outcome(
        episodes[0],
        episodes,
        num_months_cancer_prior=39,
        num_months_ci_prior=39,
        num_months_benign_follow_up=benign_follow_up_months,
    )[0]
    assert got == expected


def test_invalid_follow_up():

    date = datetime.date(2000, 1, 1)
    date2 = date + datetime.timedelta(days=2 * 365 / 12)

    episodes = [
        episode.Episode(
            id="1",
            events=events.Events(
                screening=[events.Screening(dates=[date])],
            ),
        ),
        episode.Episode(
            id="2",
            events=events.Events(
                screening=[events.Screening(dates=[date2])],
            ),
        ),
    ]

    got = episode_outcome(
        episodes[0],
        episodes,
        num_months_normal_follow_up=2,
    )[0]

    assert got == UndefinedEpisodeOutcome.InvalidFollowUp
