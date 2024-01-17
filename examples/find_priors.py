from omidb.classificationtools import has_prior


def work(clients):
    clients = list(filter(has_prior, clients))
    for client in clients:
        print(client.id)


def main():
    import omidb
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Generate a table with metadata extracted from nbss, imagedb and dicom headers files"
        )
    )

    parser.add_argument('db',
                        type=str,
                        help='Path to OMI-DB')

    args = parser.parse_args()

    db = omidb.DB(args.db)

    work(db)


if __name__ == '__main__':

    main()
