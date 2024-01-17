import csv
import omidb
import os
import argparse


def screening_image_iter(episode):
    """
    Iterate over screening images for this episode
    """
    if not (episode.events and episode.events.screening and episode.studies):
        return
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
    return filter(lambda ep: episode_has_screening_images(ep), client.episodes)


def work(path):
    """
    Iterate over OMI-DB and extract key metadata for each lesion
    """
    db = omidb.DB(path)
    for client in db:
        for ep in client.episodes:
            if ep.lesions is None:
                continue
            has_screening_images = episode_has_screening_images(ep)
            for lesion_id, lesion in ep.lesions.items():
                lesion_status = None if lesion.status is None else lesion.status.name
                lesion_grade = None if lesion.grade is None else lesion.grade.name
                lesion_desc = None if lesion.description is None else lesion.description.name
                ep_status = None if ep.status is None else ep.status.value
                # There is only some much None checking one can take
                values = [
                    client.id,
                    ep.id,
                    ep_status,
                    has_screening_images,
                    lesion_id,
                    lesion_status,
                    lesion_grade,
                    lesion_desc,
                ]

                for event in (lesion.biopsy_wide, lesion.surgery):
                    if event is None:
                        values += [None] * 4
                        continue
                    for value in (
                            event.opinion,
                            event.invasive_components,
                            event.insitu_components,
                            event.invasive_type):
                        if value is None:
                            values.append(None)
                        elif isinstance(value, list):
                            values.append(','.join(map(str, value)))
                        else:
                            values.append(value.name)
                yield(values)


def main():
    parser = argparse.ArgumentParser(
        "Extract lesion metadata for all episodes and compile the result as a CSV file"
    )
    parser.add_argument("omidb", help="Path to OMI-DB")
    parser.add_argument("output", help="CSV file name")
    args = parser.parse_args()
    with open(args.output, "w") as f:
        writer = csv.writer(f, delimiter=",")
        writer.writerow(
            (
                "ClientID",
                "EpisodeID",
                "EpisodeStatus",
                "EpisodeHasScreeningImages",
                "LesionID",
                "InvasiveOrInsitu",
                "Grade",
                "LesionDescription",
                "LesionBiopsywideOpinion",
                "LesionBiopsyInvasiveCarcinomaComponents",
                "LesionBiopsyInSituCarcinomaComponents",
                "LesionBiopsyInvasiveCarcinomaType",
                "LesionSurgerywideOpinion",
                "LesionSurgeryInvasiveCarcinomaComponents",
                "LesionSurgeryInSituCarcinomaComponents",
                "LesionSurgeryInvasiveCarcinomaType",

            )
        )
        for row in work(os.path.expanduser(args.omidb)):
            writer.writerow(row)


if __name__ == "__main__":
    main()
