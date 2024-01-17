from typing import List, Iterable, Tuple, Union, Any, Optional, Iterator
from dataclasses import dataclass
import dataclasses
import csv
import click
from .. import utilities
from ..client import Client
from ..image import Image
from ..study import Study
from ..series import Series
from ..episode import Episode
from .. import classificationtools as ct
from ..parser import DB
from loguru import logger
import datetime


@dataclass
class Config:
    db: str
    output_file: str
    link_all: bool
    clients_file: str
    log_file: str
    nbss_dir: str
    num_months_cancer_prior: Optional[int]
    num_months_ci_prior: Optional[int]
    num_months_normal_follow_up: Optional[int]
    num_months_benign_follow_up: Optional[int]


def flatten(
    clients: Iterable[Client],
    config: Config,
) -> Iterator[
    Tuple[
        Client,
        Episode,
        Optional[datetime.date],
        Optional[str],
        Optional[str],
        Optional[bool],
        Optional[Study],
        Optional[Series],
        Optional[Image],
    ]
]:
    for client in clients:
        for episode in client.episodes:
            episode_sort_date: Optional[datetime.date]
            try:
                episode_sort_date = ct._earliest_date(episode)
            except Exception:
                logger.exception(
                    f"Failed to extract sort date for {client.id} / {episode.id}"
                )
                episode_sort_date = None

            episode_outcome: Optional[str] = None
            related_episode_id: Optional[str] = None
            try:
                outcome, related_episode_id = ct.episode_outcome(
                    episode=episode,
                    all_episodes=client.episodes,
                    num_months_ci_prior=config.num_months_ci_prior,
                    num_months_cancer_prior=config.num_months_cancer_prior,
                    num_months_normal_follow_up=config.num_months_normal_follow_up,
                    num_months_benign_follow_up=config.num_months_benign_follow_up,
                )
                if outcome is not None:
                    episode_outcome = outcome.name
            except Exception:
                logger.exception(f"Failed to classify {client.id} / {episode.id}")

            post_op: Optional[bool] = None
            try:
                post_op = ct.is_post_op(episode, client.episodes)
            except Exception:
                logger.exception(
                    "Failed to identify 'post_op' status for "
                    f"{client.id} / {episode.id}"
                )
                post_op = None

            if not episode.studies:
                yield (
                    client,
                    episode,
                    episode_sort_date,
                    episode_outcome,
                    related_episode_id,
                    post_op,
                    None,
                    None,
                    None,
                )
            else:
                for study in episode.studies:
                    for series in study.series:
                        for image in series.images:
                            yield (
                                client,
                                episode,
                                episode_sort_date,
                                episode_outcome,
                                related_episode_id,
                                post_op,
                                study,
                                series,
                                image,
                            )


@dataclass
class DicomAttributes:
    Manufacturer: Optional[str] = None
    Model: Optional[str] = None
    PresentationIntentType: Optional[str] = None
    ImageLaterality: Optional[str] = None
    ViewPosition: Optional[str] = None
    ViewModCodeValue: Optional[str] = None
    ViewModCodeMeaning: Optional[str] = None
    BodyPartThicknessMM: Optional[float] = None
    PatientAgeYears: Optional[int] = None
    TransferSyntaxUID: Optional[str] = None


def extract_dicom_attributes(image: Image) -> DicomAttributes:
    """Forcefully extract dicom attributes"""

    manufacturer = utilities.try_image_attribute(image, "00080070")
    model = utilities.try_image_attribute(image, "00081090")
    presentation_intent_type = utilities.try_image_attribute(image, "00080068")
    image_laterality = utilities.try_image_attribute(image, "00200062")
    view_position = utilities.try_image_attribute(image, "00185101")
    view_mod_code_value = utilities.try_image_attribute(image, ["00540220", "00080100"])
    view_mod_code_meaning = utilities.try_image_attribute(
        image, ["00540220", "00080104"]
    )

    thickness = utilities.try_image_attribute(image, "001811A0")
    age = utilities.parse_age(image)
    transfer_syntax_uid = utilities.try_image_attribute(image, "00020010")

    return DicomAttributes(
        Manufacturer=manufacturer,
        Model=model,
        PresentationIntentType=presentation_intent_type,
        ImageLaterality=image_laterality,
        ViewPosition=view_position,
        ViewModCodeValue=view_mod_code_value,
        ViewModCodeMeaning=view_mod_code_meaning,
        BodyPartThicknessMM=thickness,
        PatientAgeYears=age,
        TransferSyntaxUID=transfer_syntax_uid,
    )


class DataWriter:
    def __init__(self) -> None:
        # Set up header
        self.rows: List[List[Any]] = [
            [
                "ClientID",
                "Site",
                "EpisodeID",
                "EpisodeSortDate",
                "EpisodeStatus",
                "EpisodeOutcome",
                "EpisodeOutcomeFutureEpisodeID",
                "EpisodeIsPostOp",
                "EpisodeType",
                "EpisodeAction",
                "EpisodeContainsMalignantOpinions",
                "EpisodeContainsBenignOpinions",
                "EpisodeOpenedDate",
                "EpisodeClosedDate",
                "ActualEpisodeOpenedYear",
                "EpisodeHasEvents",
                "StudyInstanceUID",
                "StudyDate",
                "EventType",
                "SeriesInstanceUID",
                "SOPInstanceUID",
                "NumberOfMarks",
            ]
        ]

        for field in dataclasses.fields(DicomAttributes):
            self.rows[0].append(field.name)

    def add(
        self,
        client: Client,
        episode: Episode,
        episode_sort_date: Optional[datetime.date],
        episode_outcome: Optional[str],
        episode_outcome_future_id: Optional[str],
        post_op: Optional[bool],
        study: Optional[Study],
        series: Optional[Series],
        image: Optional[Image],
    ) -> None:
        event_types: List[Union[None, str]] = [None]

        if study and study.event_type:
            event_types = [e.name for e in study.event_type]

        if image:
            tags = extract_dicom_attributes(image)
            num_marks = len(image.marks) if image.marks else 0
        else:
            tags = DicomAttributes()  # type: ignore
            num_marks = 0

        episode_status = episode.status.name if episode.status else None

        # 1 row per event
        for event_type in event_types:
            ep_action = episode.action.name if episode.action else None
            ep_type = episode.type.name if episode.type else None

            row = [
                client.id,
                client.site,
                episode.id,
                episode_sort_date,
                episode_status,
                episode_outcome,
                episode_outcome_future_id,
                post_op,
                ep_type,
                ep_action,
                episode.has_malignant_opinions,
                episode.has_benign_opinions,
                episode.opened_date,
                episode.closed_date,
                episode.actual_opened_year,
                episode.events is not None,
                study.id if study else None,
                study.date if study else None,
                event_type,
                series.id if series else None,
                image.id if image else None,
                num_marks,
            ]

            for tag in self.rows[0][len(row) :]:
                row.append(getattr(tags, tag))

            self.rows.append(row)

    def write(self, outfile: str) -> None:
        with open(outfile, "w") as f:
            writer = csv.writer(f, delimiter=",")
            writer.writerows(self.rows)


def run(config: Config) -> None:
    client_list = None
    if config.clients_file:
        with open(config.clients_file, "r") as f:
            client_list = [_.strip() for _ in f.readlines()]

    db = DB(
        config.db,
        clients=client_list,
        distinct_event_study_links=(not config.link_all),
        nbss_dir=config.nbss_dir,
    )
    writer = write_client_data(db, config)
    writer.write(config.output_file)


def write_client_data(
    clients: Iterable[Client], config: Optional[Config] = None
) -> DataWriter:
    if config is None:
        config = Config("", "", False, "", "", "", None, None, None, None)
    writer: DataWriter = DataWriter()
    for data in flatten(clients, config):
        writer.add(*data)
    return writer


@click.command("summarise")
@click.argument("db", type=click.Path(exists=True))
@click.argument("output-file", type=click.Path(exists=False))
@click.option(
    "--link-all",
    is_flag=True,
    help="Link all images to events, even if links are not unique",
)
@click.option(
    "--clients-file",
    type=click.Path(exists=True),
    help="File containing a list of clients to parse",
)
@click.option("--log-file", type=click.Path(exists=False), help="Log to this file")
@click.option(
    "--nbss-dir",
    type=click.Path(exists=False),
    help="Path to alternative directory where NBSS files can be found",
)
@click.option(
    "--num-months-cancer-prior",
    type=int,
    default=None,
    help=(
        "The maximum number of months between a malignant episode and any previous "
        "episode for a previous episode to be considered a prior."
    ),
)
@click.option(
    "--num-months-ci-prior",
    type=int,
    default=None,
    help=(
        "The maximum number of months between an interval cancer and any previous "
        "episode for a previous episode to be considered a prior."
    ),
)
@click.option(
    "--num-months-normal-follow-up",
    type=int,
    default=None,
    help="The number of months after which a second non-malignant episode must exist",
)
@click.option(
    "--num-months-benign-follow-up",
    type=int,
    default=None,
    help="The number of months after which a second non-malignant episode must exist",
)
def cli(
    db: str,
    output_file: str,
    link_all: bool,
    clients_file: str,
    log_file: str,
    nbss_dir: str,
    num_months_cancer_prior: Optional[int],
    num_months_ci_prior: Optional[int],
    num_months_normal_follow_up: Optional[int],
    num_months_benign_follow_up: Optional[int],
) -> None:
    """ "Write a csv file, OUTPUT_FILE, summarising the content of OMI-DB,
    located at DB
    """

    config = Config(
        db,
        output_file,
        link_all,
        clients_file,
        log_file,
        nbss_dir,
        num_months_cancer_prior,
        num_months_ci_prior,
        num_months_normal_follow_up,
        num_months_benign_follow_up,
    )

    logger.enable("omidb")

    if log_file:
        logger.remove()
        logger.add(log_file)

    run(config)
