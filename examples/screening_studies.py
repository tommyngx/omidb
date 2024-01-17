import csv
from loguru import logger
import omidb

logger.add("file_{time}.log", level="DEBUG")


def work(clients, fname='screening_studies.csv'):

    rows = []
    for client in clients:

        client_filt = omidb.classificationtools.filter_studies_by_event_type(
            client, 'screening', False
        )

        for ep in client_filt.episodes:
            for s in ep.studies:
                rows.append([client.id, ep.id, s.id, str(s.date)])

    if rows:
        with open(fname, 'w') as f:
            writer = csv.writer(f, delimiter=',')
            writer.writerow(
                ['client', 'episode', 'screening_study', 'study_date']
            )
            writer.writerows(rows)


def main():
    import omidb
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Generate a table of screening studies"
        )
    )

    parser.add_argument('db',
                        type=str,
                        help='Path to OMI-DB')

    parser.add_argument('clients',
                        type=str,
                        help='File containing a list of clients')

    parser.add_argument('filename',
                        type=str,
                        help='Name of the csv file to write to')

    args = parser.parse_args()

    if args.clients:
        with open(args.clients, 'r') as f:
            clients = [_.strip() for _ in f]
    else:
        clients = []

    db = omidb.DB(args.db, clients=clients)

    work(db, args.filename)


if __name__ == '__main__':

    main()
