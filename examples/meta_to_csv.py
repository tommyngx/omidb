import time


def flatten(clients):
    '''
    I know, I know...
    '''
    for client in clients:
        for episode in client.episodes:
            for study in episode.studies:
                for series in study.series:
                    for image in series.images:
                        yield(client,
                              episode,
                              study,
                              series,
                              image)


def clients_to_csv(clients, filename):
    import csv
    import json

    table = [
        ['Client',
         'Episode',
         'Study',
         'Series',
         'Image',
         'Mark',
         'Manufacturer',
         'Mass',
         'MassClassification',
         'WithCalcification',
         ]
    ]

    then = time.time()

    for client, episode, study, series, image in flatten(clients):

        # The tag you're interested in
        try:
            manufacturer = image.attributes['00080070']['Value'][0]
        except json.decoder.JSONDecodeError:
            print(f'Failed to decode JSON for image {image.id}')
            manufacturer = None

        if image.marks:
            for mark in image.marks:
                mark_id = mark.id
                mass = [mark.mass, mark.mass_classification,
                        mark.calcifications]
        else:
            mark_id = None
            mass = [None, None, None]

        table.append(
            [client.id, episode.id, study.id, series.id, image.id, mark_id, manufacturer] +
            mass
        )

    print(f"Time to populate table: {time.time() - then} s")

    with open(filename, "w") as f:
        writer = csv.writer(f)
        writer.writerows(table)


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

    parser.add_argument('filename',
                        type=str,
                        help='Name of the csv file generated')

    args = parser.parse_args()

    db = omidb.DB(args.db)

    then = time.time()
    clients = [c for c in db]
    print(f"Time to parse DB: {time.time() - then} s")

    clients_to_csv(clients, args.filename)


if __name__ == '__main__':

    main()
