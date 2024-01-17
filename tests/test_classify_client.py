import omidb


def get_ci_ep() -> omidb.episode.Episode:
    return omidb.episode.Episode(
        "a", studies=None, events=None, type=omidb.episode.Type.CI
    )


def get_benign_ep() -> omidb.episode.Episode:

    event = omidb.events.BaseEvent(left_opinion=omidb.events.SideOpinion.OB)

    events = omidb.events.Events(surgery=event)
    return omidb.episode.Episode("a", events, None)  # type: ignore


def get_malignant_ep() -> omidb.episode.Episode:

    event = omidb.events.BaseEvent(left_opinion=omidb.events.SideOpinion.OM)

    events = omidb.events.Events(surgery=event)
    return omidb.episode.Episode("a", events, None)  # type: ignore


def get_ep() -> omidb.episode.Episode:

    event = omidb.events.BaseEvent(left_opinion=omidb.events.SideOpinion.ON)

    events = omidb.events.Events(assessment=event)
    return omidb.episode.Episode("a", events, None)  # type: ignore


def test_classify_client() -> None:

    n_test = ([get_ep()], omidb.client.Status.N)

    b_test = ([get_ep(), get_benign_ep()], omidb.client.Status.B)

    m_test = ([get_ep(), get_benign_ep(), get_malignant_ep()], omidb.client.Status.M)

    ci_test = (
        [get_ep(), get_benign_ep(), get_malignant_ep(), get_ci_ep()],
        omidb.client.Status.CI,
    )

    for episodes, expected in [n_test, b_test, m_test, ci_test]:

        client = omidb.client.Client(
            "demd1", site=None, episodes=episodes  # type:ignore
        )

        assert client.status == expected
