import omidb


def test_episode_has_benign_opinions_false() -> None:

    for opinion in (
        omidb.events.SideOpinion.OM,
        omidb.events.SideOpinion.ON,
        omidb.events.SideOpinion.OS,
        omidb.events.SideOpinion.OU,
    ):

        events = omidb.events.Events(
            surgery=omidb.events.BaseEvent(left_opinion=opinion),
        )

        e = omidb.episode.Episode("a", events, None)  # type: ignore
        assert not e.has_benign_opinions


def test_episode_has_malignant_opinions_false() -> None:

    for opinion in (
        omidb.events.SideOpinion.OB,
        omidb.events.SideOpinion.ON,
        omidb.events.SideOpinion.OS,
        omidb.events.SideOpinion.OU,
    ):

        events = omidb.events.Events(
            surgery=omidb.events.BaseEvent(left_opinion=opinion),
        )

        e = omidb.episode.Episode("a", events, None)  # type: ignore
        assert not e.has_malignant_opinions


def test_episode_has_benign_opinions_true() -> None:

    event_ob = omidb.events.BaseEvent(left_opinion=omidb.events.SideOpinion.OB)
    event_om = omidb.events.BaseEvent(left_opinion=omidb.events.SideOpinion.OM)
    for event1, event2 in ((event_ob, event_om), (event_om, event_ob)):
        events = omidb.events.Events(surgery=event1, biopsy_wide=event2)
        e = omidb.episode.Episode("a", events, None)  # type: ignore
        assert e.has_benign_opinions


def test_episode_has_malignant_opinions_true() -> None:

    event_ob = omidb.events.BaseEvent(left_opinion=omidb.events.SideOpinion.OB)
    event_om = omidb.events.BaseEvent(left_opinion=omidb.events.SideOpinion.OM)

    for event1, event2 in ((event_ob, event_om), (event_om, event_ob)):
        events = omidb.events.Events(surgery=event1, biopsy_wide=event2)
        e = omidb.episode.Episode("a", events, None)  # type: ignore
        assert e.has_malignant_opinions


def test_episode_has_benign_opinions_side() -> None:

    left = omidb.events.BaseEvent(left_opinion=omidb.events.SideOpinion.OB)
    right = omidb.events.BaseEvent(right_opinion=omidb.events.SideOpinion.OB)

    for side in (left, right):

        events_surgery = omidb.events.Events(surgery=side)
        events_biopsy = omidb.events.Events(biopsy_wide=side)

        for events in (events_surgery, events_biopsy):
            e = omidb.episode.Episode("a", events, None)  # type: ignore
            assert e.has_benign_opinions


def test_episode_has_malignant_opinions_side() -> None:

    left = omidb.events.BaseEvent(left_opinion=omidb.events.SideOpinion.OM)
    right = omidb.events.BaseEvent(right_opinion=omidb.events.SideOpinion.OM)

    for side in (left, right):

        events_surgery = omidb.events.Events(surgery=side)
        events_biopsy = omidb.events.Events(biopsy_wide=side)

        for events in (events_surgery, events_biopsy):
            e = omidb.episode.Episode("a", events, None)  # type: ignore
            assert e.has_malignant_opinions
