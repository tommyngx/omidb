import argparse
import omidb
from omidb.classificationtools import episode_outcome, EpisodeOutcome
from omidb.episode import Status


def episode_has_marks(episode: omidb.episode.Episode) -> bool:
    for study in episode.studies:
        for series in study.series:
            for image in series.images:
                if image.marks:
                    return True
    return False


def main():
    parser = argparse.ArgumentParser(
        prog="omidb-bprior",
        description=(
            "Identify benign cases that occured directly before a "
            "malignant episode. Writes a CSV file to stdout."
        ),
    )

    parser.add_argument(
        "image_json_path",
        help="Path to the data dir containing client folders of JSONs",
    )
    parser.add_argument(
        "nbss_json_path",
        help="Path to the data dir containing client folders of NBSS JSONs",
    )
    parser.add_argument(
        "--clients_file", help="File contianing a list of clients to parse"
    )

    parser.add_argument(
        "--num_months_cancer_prior",
        help="Number of months for an episode to be considered a prior",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    clients = []
    if args.clients_file is not None:
        with open(args.clients_file, "r") as f:
            for case in f.readlines():
                clients.append(case.rstrip())

    db = omidb.DB(
        args.image_json_path,
        clients=clients,
        nbss_dir=args.nbss_json_path,
        distinct_event_study_links=False,
    )

    header_shown = False
    records = []
    for client in db:
        for episode in client.episodes:
            # Only interested in MP, M, B or CIP episodes
            try:
                outcome, _ = episode_outcome(
                    episode,
                    client.episodes,
                    num_months_cancer_prior=args.num_months_cancer_prior,
                )
                outcome_s = outcome.name
            except ValueError:
                continue

            if (
                (outcome == EpisodeOutcome.MP)
                and (episode.status == Status.B)
                and episode.studies  # must have images
            ):
                marks = episode_has_marks(episode)
                records.append(
                    f"{client.id},{episode.id},{episode.status}{outcome_s},{marks}"
                )

        if records:
            if not header_shown:
                print("ClientID,EpisodeID,EpisodeStatus,EpisodeOutcome,EpisodeHasMarks")
                header_shown = True
            for record in records:
                print(record)
        records = []


if __name__ == "__main__":
    main()
