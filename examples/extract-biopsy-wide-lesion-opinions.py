import json
import omidb
import os
import argparse
from loguru import logger
logger.enable("omidb")


def screening_image_iter(episode):
    """
    Iterate over screening images for this episode
    """
    if not (episode.events and episode.events.screening and episode.studies):
        return None
    for study in episode.studies:
        if (
            study.event_type
            and (len(study.event_type) == 1)
            and (omidb.events.Event.screening in study.event_type)
        ):
            for series in study.series:
                for image in series.images:
                    yield (image)


def episode_has_screening_images(episode):
    """
    Returns `True` if this episode contains screening images.
    `False` otherwise.
    """
    for _ in screening_image_iter(episode):
        return True
    return False


def screening_eps(client):
    """
    Return an iterator of screening episodes with imaging
    """
    return filter(
        lambda ep: episode_has_screening_images(ep),
        client.episodes
    )


def biopsy_wide_lesion_side_opinions(ep):
    """
    Returns `None` if no biopsy wide event. Otherwise, returns a dictionary
    containing the biopsy wide opinions for the left `L` and right `R` breast.
    Expect multiple values if there are multiple lesions within one breast.
    """
    if ep.events.biopsy_wide is None:
        return None
    result = {'L': [], 'R': []}
    for _, lesion in ep.lesions.items():
        if lesion.biopsy_wide is None:
            continue
        opinion = None if lesion.biopsy_wide.opinion is None else lesion.biopsy_wide.opinion.name
        result[lesion.side.name].append(opinion)
    return result


def biopsy_lesion_data(path, with_ids):
    """
    Extract the screening opinion and biopsy-wide opinions for all screening
    episodes for which imaging are available
    """
    db = omidb.DB(path)
    clients = []
    for client in db:
        logger.debug(f"Processing client {client.id}")
        client_data = []
        for ep in screening_eps(client):
            logger.debug(f"Processing episode {ep.id}")
            # Skip clients with multiple screens
            if len(ep.events.screening) > 1:
                continue
            ops = biopsy_wide_lesion_side_opinions(ep)
            screen = ep.events.screening[0]
            ep_data = {
                "ScreeningOpinion": {
                    "L": None if screen.left_opinion is None else
                    screen.left_opinion.value,
                    "R": None if screen.right_opinion is None else
                    screen.right_opinion.value,
                },
                "BiopsyWideOpinionCodes": ops,
            }
            if with_ids:
                ep_data["ClientID"] = client.id
                ep_data["EpisodeID"] = ep.id
            client_data.append(ep_data)
        if client_data:
            clients.append(client_data)
    return clients


def main():
    parser = argparse.ArgumentParser(
        (
            "Extract biopsy opinion codes for screening episodes with imaging. "
            "The data are compiled as a list of nested lists and stored as a JSON "
            "file, where each entry represents a list of screening episodes "
            "for a given client."
        )
    )
    parser.add_argument("omidb", help="Path to OMI-DB")
    parser.add_argument("output", help="JSON file name")
    parser.add_argument(
        "--with-ids", help="Include client and episode IDs", action="store_true")
    args = parser.parse_args()
    json_path = os.path.expanduser(args.output)
    data = biopsy_lesion_data(os.path.expanduser(args.omidb), args.with_ids)
    with open(json_path, "w") as f:
        json.dump(data, f)


if __name__ == '__main__':
    main()
