import omidb
import argparse
import json


def main():

    parser = argparse.ArgumentParser(
        description=(
            "OMI-DB counts"
        )
    )

    parser.add_argument('db',
                        type=str,
                        help='Path to OMI-DB')

    parser.add_argument('--clients',
                        type=str,
                        required=False,
                        help='File containing a list of clients')

    args = parser.parse_args()

    if args.clients:
        with open(args.clients, 'r') as f:
            clients = [_.strip() for _ in f]
    else:
        clients = None

    counts = {
        'clients': 0,
        'episodes': 0,
        'studies': 0,
        'series': 0,
        'images': 0,
        'marks': 0,
    }
    for client in omidb.DB(args.db, clients=clients):
        counts['clients'] += 1
        for episode in client.episodes:
            counts['episodes'] += 1
            for study in episode.studies:
                counts['studies'] += 1
                for series in study.series:
                    counts['series'] += 1
                    for image in series.images:
                        counts['images'] += 1
                        for mark in image.marks:
                            counts['marks'] += 1

    print(json.dumps(counts, indent=2))


if __name__ == '__main__':

    main()
