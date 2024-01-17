from typing import List
import datetime
import omidb
from omidb.classificationtools import has_prior


def create_client(years: List[int], ascending: bool = True) -> omidb.client.Client:

    events = omidb.events.Events(
        surgery=omidb.events.BaseEvent(left_opinion=omidb.events.SideOpinion.OM)
    )

    episodes = [
        omidb.episode.Episode(
            "a",
            omidb.events.Events(),
            None,
            opened_date=datetime.date(2013, 1, 1),  # type: ignore
        ),
        omidb.episode.Episode(
            "b",
            omidb.events.Events(),
            None,
            opened_date=datetime.date(2014, 1, 1),  # type: ignore
        ),
        omidb.episode.Episode(
            "c",
            omidb.events.Events(),
            None,
            opened_date=datetime.date(2015, 1, 1),  # type: ignore
        ),
    ]

    if not ascending:
        episodes.reverse()

    for year in years:
        for episode in episodes:
            if episode.opened_date.year == year:  # type: ignore
                episode.events = events

    return omidb.client.Client("abc1", episodes, "site")


def test_has_prior_event() -> None:

    for ascending in (True, False):

        client = create_client([2013], ascending)
        assert not has_prior(client)

        client = create_client([2014], ascending)
        assert has_prior(client)

        client = create_client([2015], ascending)
        assert has_prior(client)

        client = create_client([2013, 2014], ascending)
        assert not has_prior(client)

        client = create_client([2013, 2015], ascending)
        assert has_prior(client)
