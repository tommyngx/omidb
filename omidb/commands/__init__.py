import click
from . import summarise


@click.group()
def entry_point() -> None:
    pass


def main() -> None:
    entry_point.add_command(summarise.cli)
    entry_point()
