import datetime
import dataclasses
from typing import List, Dict, Optional, Any
from loguru import logger
from . import utilities
from .client import Client
from .episode import Episode
from . import episode
from . import image as im
from .study import Study
from .series import Series
from .lesion import (
    Lesion,
    LesionDescription,
    LesionAssessment,
    LesionSurgery,
    LesionClinical,
    LesionIntervalCancer,
    LesionBiopsyWide,
    LesionBiopsyFine,
    LesionPosition,
    Side,
    InvasiveCarcinomaComponent,
    HistologicalGrade,
    InSituCarcinomaComponent,
    InvasiveCarcinomaType,
    DCISGrade,
    MalignancyType,
)
from .mark import (
    BenignClassification,
    Conspicuity,
    MassClassification,
    BoundingBox,
    Mark,
)

from .events import (
    Event,
    Events,
    BreastScreeningData,
    Screening,
    BaseEvent,
    Opinion,
    SideOpinion,
)


class ClientParser:
    def __init__(
        self,
        id: str,
        nbss: Dict[str, Any],
        imagedb: Dict[str, Any],
        studies: List[str] = [],
        distinct_event_study_links: bool = True,
        json_loader: Optional[im.JsonLoaderFunc] = None,
        dcm_loader: Optional[im.DicomLoaderFunc] = None,
    ):
        self.id = id
        self.nbss = nbss
        self.imagedb = imagedb
        self.studies = studies
        self.distinct_event_study_links = distinct_event_study_links
        self.json_loader = json_loader
        self.dcm_loader = dcm_loader
        self._episode_id: Optional[str] = None

    def __call__(self) -> Client:
        episodes = self.parse_episodes()
        return Client(id=self.id, episodes=episodes, site=self.imagedb["Site"])

    def logmsg(self, msg: str) -> str:
        _msg = f"{self.id}"
        if self._episode_id is not None:
            _msg = f"{_msg}/Episode {self._episode_id}"
        _msg = f"{_msg}: {msg}"
        return _msg

    def parse_episodes(self) -> List[Episode]:
        events: Dict[str, Optional[Events]] = {}
        for episode_id, nbss_episode in self.nbss.items():
            if isinstance(nbss_episode, dict):
                events[episode_id] = self.parse_events(nbss_episode)

        episode_studies = self.studies_by_episode(events)

        out = []

        for episode_id, episode_events in events.items():
            self._episode_id = episode_id

            this_episodes_studies = episode_studies.get(episode_id, [])

            if not this_episodes_studies:
                logger.warning(self.logmsg("Episode in NBSS but not in IMAGEDB"))
            elif self.distinct_event_study_links and episode_events is not None:
                self.ensure_distinct_study_event_links(
                    this_episodes_studies, episode_events
                )

            nbss_episode = self.nbss[episode_id]
            is_closed = nbss_episode.get("EpisodeIsClosed") == "Y"

            ep_type: Optional[episode.Type] = utilities.nbss_str_to_enum(
                nbss_episode.get("EpisodeType"), episode.Type
            )

            ep_action: Optional[episode.Action] = utilities.nbss_str_to_enum(
                nbss_episode.get("EpisodeAction"), episode.Action
            )

            opened_date = utilities.date_or_none(nbss_episode, "EpisodeOpenedDate")
            closed_date = utilities.date_or_none(nbss_episode, "EpisodeClosedDate")
            diagnosis_date = utilities.date_or_none(
                nbss_episode, "IntervalCancerDateOfDiagnosis"
            )

            actual_opened_year = (
                int(nbss_episode.get("ActualEpisodeOpenedYear"))
                if nbss_episode.get("ActualEpisodeOpenedYear", None)
                else None
            )

            lesions = self._parse_lesions(nbss_episode)

            out.append(
                Episode(
                    id=episode_id,
                    events=episode_events,
                    studies=this_episodes_studies,
                    type=ep_type,
                    action=ep_action,
                    is_closed=is_closed,
                    lesions=lesions,
                    actual_opened_year=actual_opened_year,
                    opened_date=opened_date,
                    closed_date=closed_date,
                    diagnosis_date=diagnosis_date,
                )
            )

            self._episode_id = None
        return out

    def studies_by_episode(
        self,
        events: Dict[str, Optional[Events]],
    ) -> Dict[str, List[Study]]:
        # Studies for each episode
        episode_studies: Dict[str, List[Study]] = {}

        if not self.has_studies():
            return episode_studies

        for study_id, study_data in self.imagedb["STUDIES"].items():
            logger.info(
                self.logmsg(f"Attempting to link study {study_id} to an episode")
            )

            if self.studies is not None and study_id not in self.studies:
                logger.info(
                    self.logmsg(
                        f"{study_id} found in ImageDB, but not "
                        "in provided list of studies, skipping"
                    )
                )
                continue

            study_date = utilities.date_or_none(study_data, "StudyDate")

            if study_date is None:
                logger.warning(self.logmsg(f"{study_id} has no study date"))
            # Try to extract episode ID by study-date <->event-date
            elif (
                ("EpisodeID" not in study_data)
                or (not study_data["EpisodeID"])
                or (study_data["EpisodeID"] not in events)
            ):
                logger.warning(
                    self.logmsg(
                        f"Episode {study_data.get('EpisodeID')} (in IMAGEDB) not found"
                        f" in NBSS for study {study_id}, attempting link via event"
                        " dates (will replace episode ID)"
                    )
                )

                episode_id = self.find_episode_id_by_event_dates(study_date, events)

                if episode_id is not None:
                    study_data["EpisodeID"] = episode_id

            # If stil not episode ID, skip
            if ("EpisodeID" not in study_data) or (not study_data["EpisodeID"]):
                logger.error(f"EpisodeID not found for study {study_id}, skipping")

                continue

            # if event and (study_date in event_dates): fallback to episode id
            matched_events: List[Event] = []
            if study_date is not None and study_data["EpisodeID"] in events:
                matched_events = self.match_events(
                    events[study_data["EpisodeID"]],
                    study_date,
                )
            else:
                logger.warning(
                    self.logmsg(
                        f"Episode {study_data['EpisodeID']} (IMAGEDB) has no events"
                        "(episode not found in NBSS)"
                    )
                )
                continue

            # Now add studies to the episode
            study = Study(
                id=study_id,
                series=self.parse_series(study_id, study_data),
                date=study_date,
                event_type=matched_events,
            )

            if study_data["EpisodeID"] not in episode_studies:
                episode_studies[study_data["EpisodeID"]] = [study]
            else:
                episode_studies[study_data["EpisodeID"]].append(study)

        return episode_studies

    def parse_series(
        self,
        study_iuid: str,
        study_data: Dict[str, Any],
    ) -> List[Series]:
        series_list = []

        for series, series_dic in study_data.items():
            if not (isinstance(series_dic, dict) and utilities.IUID_REG.match(series)):
                continue

            image_list = [
                im for im in series_dic.keys() if utilities.IUID_REG.match(im)
            ]

            images = []
            for image in image_list:
                marks: List[Mark] = []

                image_marks_data = series_dic.get(image)
                if isinstance(image_marks_data, dict):
                    for _, mark_data in image_marks_data.items():
                        try:
                            marks.append(self._parse_mark(mark_data))
                        except Exception:
                            logger.exception(
                                f"Failed to parse mark data of {self.id} {image}.dcm"
                            )
                            continue

                args = im.LoaderParams(self.id, study_iuid, series, image)

                if self.dcm_loader is not None:
                    dcm_loader = im.DicomLoader(args, self.dcm_loader)
                else:
                    dcm_loader = None

                if self.json_loader is not None:
                    json_loader = im.JsonLoader(args, self.json_loader)
                else:
                    json_loader = None

                images.append(
                    im.Image(
                        id=image,
                        dcm_loader=dcm_loader,
                        json_loader=json_loader,
                        marks=marks,
                    )
                )

            series_list.append(Series(id=series, images=images))
        return series_list

    def has_studies(self) -> bool:
        if ("STUDIES" not in self.imagedb) or (
            not isinstance(self.imagedb["STUDIES"], dict)
        ):
            logger.error("No studies listed in IMAGEDB for client {self.id]}")
            return False
        return True

    def match_events(
        self,
        episode_events: Optional[Events],
        study_date: datetime.date,
    ) -> List[Event]:
        matched_events: List[Event] = []
        if episode_events is None:
            return matched_events

        for field in dataclasses.fields(episode_events):
            event_list = getattr(episode_events, field.name)
            if event_list is None:
                continue

            if not isinstance(event_list, list):
                event_list = [event_list]

            for e in event_list:
                if study_date in e.dates:
                    matched_events.append(getattr(Event, field.name))

        if not matched_events:
            logger.warning(self.logmsg(f"No events match study date {study_date}"))

            for field in dataclasses.fields(episode_events):
                event = getattr(episode_events, field.name)
                if event is None:
                    continue
                matched_events.append(getattr(Event, field.name))
                logger.warning(
                    self.logmsg(
                        f"Linked {field.name} event to study by episode ID only"
                    )
                )

        if len(matched_events) > 1:
            logger.warning(self.logmsg("Multiple events linked"))
            if self.distinct_event_study_links:
                logger.info(self.logmsg("Dropping matched events as not distinct"))
                matched_events = []
        return matched_events

    def find_episode_id_by_event_dates(
        self, study_date: datetime.date, events: Dict[str, Any]
    ) -> Optional[str]:
        for episode_id, episode_events in events.items():
            if episode_events is None:
                continue
            for field in dataclasses.fields(episode_events):
                event = getattr(episode_events, field.name)
                if event is None:
                    continue

                if isinstance(event, list):
                    event_dates = [date for e in event for date in e.dates]
                else:
                    event_dates = event.dates

                if event and (study_date in event_dates):
                    logger.info(
                        self.logmsg(f"Linked study date {study_date} to {episode_id}")
                    )
                    return episode_id
        return None

    def ensure_distinct_study_event_links(
        self, studies: List[Study], events: Optional[Events]
    ) -> None:
        """
        Filters (mutates) the `event_type` property of an episode's `studies` such
        that studies-event links are distinct.
        """

        for idx, study1 in enumerate(studies):
            for study2 in studies[idx:]:
                if study1 == study2:
                    continue

                # Two studies have the same date, drop any links
                if study1.date == study2.date:
                    logger.warning(
                        self.logmsg(
                            "Dropping events linked to "
                            f"{study1.id} and {study2.id} as same date "
                        )
                    )
                    study1.event_type = []
                    study2.event_type = []
                    continue

                # Two studies have the different dates,
                # but linked to same event
                if study1.event_type and study1.event_type == study2.event_type:
                    event_list = getattr(events, study1.event_type[0].name)

                    if not isinstance(event_list, list):
                        event_list = [event_list]

                    # Pool the dates if multiple screens...
                    event_dates = [date for e in event_list for date in e.dates]

                    if study1.date not in event_dates:
                        logger.warning(
                            self.logmsg(f"Dropping events linked to {study1.id}")
                        )

                        study1.event_type = []

                    if study2.date not in event_dates:
                        logger.warning(
                            self.logmsg(f"Dropping events linked to {study2.id}")
                        )
                        study2.event_type = []

    def parse_events(self, episode_data: Dict[str, Any]) -> Optional[Events]:
        event_kwargs = {
            "screening": episode_data.get("SCREENING", None),
            "assessment": episode_data.get("ASSESSMENT", None),
            "biopsy_wide": episode_data.get("BIOPSYWIDE", None),
            "biopsy_fine": episode_data.get("BIOPSYFINE", None),
            "clinical": episode_data.get("CLINICAL", None),
            "surgery": episode_data.get("SURGERY", None),
        }

        has_events = False
        for key, value in event_kwargs.items():
            if value is None:
                continue

            has_events = True
            # SCREENING must exist in order to parse OTHERSCREENING
            if key == "screening":
                event_kwargs["screening"] = [self.parse_screening_event(value)]

                other_screening = episode_data.get("OTHERSCREENING", None)
                if other_screening is not None:
                    for _, screen in other_screening.items():
                        event_kwargs["screening"].append(
                            self.parse_screening_event(screen)
                        )
            else:
                event_kwargs[key] = self.parse_base_event(value)

        if has_events:
            return Events(**event_kwargs)
        return None

    def parse_base_event(self, data: Dict[str, Any]) -> BaseEvent:
        dates: List[datetime.date] = []

        for _, side in enumerate(["L", "R"]):
            side_data = data.get(side)

            if not side_data:
                continue

            for _, lesion in side_data.items():
                if lesion.get("DatePerformed"):
                    date = utilities.date_or_none(lesion, "DatePerformed")
                    if date is not None and date not in dates:
                        dates.append(date)

        # Some events may not have lesions due to null ID
        # so add higher-level dateperformed to improve linking
        date = utilities.date_or_none(data, "dateperformed")
        if date is not None and date not in dates:
            dates.append(date)

        left_opinion = utilities.nbss_str_to_enum(data.get("left_opinion"), SideOpinion)

        right_opinion = utilities.nbss_str_to_enum(
            data.get("right_opinion"), SideOpinion
        )

        return BaseEvent(
            left_opinion=left_opinion, right_opinion=right_opinion, dates=dates
        )

    def parse_screening_event(self, data: Dict[str, Any]) -> Screening:
        breast_data: List[Optional[BreastScreeningData]] = [None, None]
        dates: List[datetime.date] = []

        for i, side in enumerate(["L", "R"]):
            side_data = data.get(side)

            if not side_data:
                continue

            date = utilities.date_or_none(side_data, "DateTaken")
            if date is not None and date not in dates:
                dates.append(date)

            opinion: Optional[Opinion] = utilities.nbss_str_to_enum(
                side_data.get("Opinion"), Opinion
            )

            breast_data[i] = BreastScreeningData(
                date=date,
                equipment_make_model=side_data.get("EquipmentMakeModel"),
                opinion=opinion,
            )

        left_opinion: Optional[SideOpinion] = utilities.nbss_str_to_enum(
            data.get("left_opinion"), SideOpinion
        )

        right_opinion: Optional[SideOpinion] = utilities.nbss_str_to_enum(
            data.get("right_opinion"), SideOpinion
        )

        return Screening(
            left_opinion=left_opinion,
            right_opinion=right_opinion,
            left=breast_data[0],
            right=breast_data[1],
            dates=dates,
        )

    def _parse_lesions(self, episode_data: Dict[str, Any]) -> Dict[str, Lesion]:
        lesions_data = episode_data.get("LESION")
        lesions: Dict[str, Lesion] = {}

        if lesions_data is None:
            return lesions

        for side in ["L", "R"]:
            side_data = lesions_data.get(side)
            if side_data is None:
                continue

            for lesion_id, lesion_data in side_data.items():
                lesion = Lesion(
                    id=lesion_id,
                    side=utilities.nbss_str_to_enum(side, Side),
                    cyst_aspirated=lesion_data.get("CystAspirated", False) == "Y",
                    description=utilities.nbss_str_to_enum(
                        lesion_data.get("LesionDescription"), LesionDescription
                    ),
                    position=utilities.nbss_str_to_enum(
                        lesion_data.get("LesionPosition"), LesionPosition
                    ),
                    notes=lesion_data.get("LesionNotes"),
                    assessment=self._parse_assessment_lesion(
                        episode_data, side, lesion_id
                    ),
                    surgery=self._parse_surgery_lesion(episode_data, side, lesion_id),
                    clinical=self._parse_clinical_lesion(episode_data, side, lesion_id),
                    biopsy_wide=self._parse_biopsy_wide_lesion(
                        episode_data, side, lesion_id
                    ),
                    biopsy_fine=self._parse_biopsy_fine_lesion(
                        episode_data, side, lesion_id
                    ),
                    interval_cancer=self._parse_interval_cancer_lesion(
                        episode_data, side, lesion_id
                    ),
                )

                lesions[lesion_id] = lesion

        return lesions

    def _parse_assessment_lesion(
        self,
        episode_data: Dict[str, Any],
        side: str,
        lesion_id: str,
    ) -> Optional[LesionAssessment]:
        try:
            data = episode_data["ASSESSMENT"][side][lesion_id]
        except KeyError:
            return None

        date = utilities.date_or_none(data, "DatePerformed")
        return LesionAssessment(date=date)

    def _parse_surgery_lesion(
        self,
        episode_data: Dict[str, Any],
        side: str,
        lesion_id: str,
    ) -> Optional[LesionSurgery]:
        try:
            data = episode_data["SURGERY"][side][lesion_id]
        except Exception:
            return None

        date = utilities.date_or_none(data, "DatePerformed")

        ivcmps: List[InvasiveCarcinomaComponent] = (
            utilities.nbss_str_to_enum(
                data.get("InvasiveComponents"),
                InvasiveCarcinomaComponent,
                "InvasiveComponents",
            )
            or []
        )

        iscmps: List[InSituCarcinomaComponent] = (
            utilities.nbss_str_to_enum(
                data.get("InSituComponents"),
                InSituCarcinomaComponent,
                "InSituComponents",
            )
            or []
        )

        return LesionSurgery(
            date=date,
            invasive_components=ivcmps,
            disease_grade=utilities.nbss_str_to_enum(
                data.get("DiseaseGrade"), HistologicalGrade
            ),
            invasive_type=utilities.nbss_str_to_enum(
                data.get("InvasiveType"),
                InvasiveCarcinomaType,
            ),
            insitu_components=iscmps,
            dcis_grade=utilities.nbss_str_to_enum(data.get("DcisGrade"), DCISGrade),
            opinion=utilities.nbss_str_to_enum(data.get("Opinion"), Opinion),
        )

    def _parse_clinical_lesion(
        self,
        episode_data: Dict[str, Any],
        side: str,
        lesion_id: str,
    ) -> Optional[LesionClinical]:
        try:
            data = episode_data["CLINICAL"][side][lesion_id]
        except KeyError:
            return None

        return LesionClinical(
            date=utilities.date_or_none(data, "DatePerformed"),
            opinion=utilities.nbss_str_to_enum(data.get("Opinion"), Opinion),
        )

    def _parse_biopsy_fine_lesion(
        self,
        episode_data: Dict[str, Any],
        side: str,
        lesion_id: str,
    ) -> Optional[LesionBiopsyFine]:
        try:
            data = episode_data["BIOPSYFINE"][side][lesion_id]
        except KeyError:
            return None

        return LesionBiopsyFine(
            date=utilities.date_or_none(data, "DatePerformed"),
            opinion=utilities.nbss_str_to_enum(data.get("Opinion"), Opinion),
        )

    def _parse_biopsy_wide_lesion(
        self,
        episode_data: Dict[str, Any],
        side: str,
        lesion_id: str,
    ) -> Optional[LesionBiopsyWide]:
        try:
            data = episode_data["BIOPSYWIDE"][side][lesion_id]
        except KeyError:
            return None

        ivcmps: List[InvasiveCarcinomaComponent] = (
            utilities.nbss_str_to_enum(
                data.get("InvasiveComponents"),
                InvasiveCarcinomaComponent,
                "InvasiveComponents",
            )
            or []
        )

        iscmps: List[InSituCarcinomaComponent] = (
            utilities.nbss_str_to_enum(
                data.get("InSituComponents"),
                InSituCarcinomaComponent,
                "InSituComponents",
            )
            or []
        )

        return LesionBiopsyWide(
            date=utilities.date_or_none(data, "DatePerformed"),
            invasive_components=ivcmps,
            disease_grade=utilities.nbss_str_to_enum(
                data.get("DiseaseGrade"), HistologicalGrade
            ),
            invasive_type=utilities.nbss_str_to_enum(
                data.get("InvasiveType"), InvasiveCarcinomaType
            ),
            insitu_components=iscmps,
            dcis_grade=utilities.nbss_str_to_enum(data.get("DcisGrade"), DCISGrade),
            malignant_type=utilities.nbss_str_to_enum(
                data.get("MalignancyType"),
                MalignancyType,
            ),
            opinion=utilities.nbss_str_to_enum(data.get("Opinion"), Opinion),
        )

    def _parse_interval_cancer_lesion(
        self,
        episode_data: Dict[str, Any],
        side: str,
        lesion_id: str,
    ) -> Optional[LesionIntervalCancer]:
        try:
            data = episode_data["INTERVALCANCER"][side][lesion_id]
        except KeyError:
            return None

        return LesionIntervalCancer(date=utilities.date_or_none(data, "DatePerformed"))

    def _parse_mark(self, mark_data: Dict[str, Any]) -> Mark:
        args: Dict[str, Any] = {}

        for param_name, key in zip(
            (
                "architectural_distortion",
                "dystrophic_calcification",
                "fat_necrosis",
                "focal_asymmetry",
                "mass",
                "suspicious_calcifications",
                "milk_of_calcium",
                "other_benign_cluster",
                "plasma_cell_mastitis",
                "benign_skin_feature",
                "calcifications",
                "suture_calcification",
                "vascular_feature",
            ),
            (
                "ArchitecturalDistortion",
                "Dystrophic",
                "FatNecrosis",
                "FocalAsymmetry",
                "Mass",
                "SuspiciousCalcifications",
                "MilkOfCalcium",
                "OtherBenignCluster",
                "PlasmaCellMastitis",
                "Skin",
                "WithCalcification",
                "SutureCalcification",
                "Vascular",
            ),
        ):
            args[param_name] = True if mark_data.get(key, None) else None

        args["benign_classification"] = utilities.nbss_str_to_enum(
            mark_data.get("BenignClassification"), BenignClassification
        )

        args["conspicuity"] = utilities.nbss_str_to_enum(
            mark_data.get("Conspicuity"), Conspicuity
        )

        args["mass_classification"] = utilities.nbss_str_to_enum(
            mark_data.get("MassClassification"), MassClassification
        )

        try:
            ids = mark_data["LinkedNBSSLesionNumber"].split(",")
            args["lesion_ids"] = set([str(int(_)) for _ in ids])
        except Exception:
            args["lesion_ids"] = None

        args["id"] = str(mark_data["MarkID"])

        args["boundingBox"] = BoundingBox(
            x1=int(mark_data["X1"]),
            y1=int(mark_data["Y1"]),
            x2=int(mark_data["X2"]),
            y2=int(mark_data["Y2"]),
        )

        return Mark(**args)
