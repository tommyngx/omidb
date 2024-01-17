import omidb
from .events import Event
from .episode import Episode, Type, Status, _validate_events
import copy
from typing import Optional, List, Union, Tuple
import datetime
import dataclasses
import enum
from math import ceil


def has_prior(client: omidb.client.Client) -> bool:
    """
    Returns ``True`` if ``client`` has a non-malignant episode earlier than a
    malignant episode; ``False`` otherwise.

    :param client: A classified client with more than one episode
    """

    if client.status != omidb.client.Status.M:
        return False

    nm_date = None  # earliest non-malignant date
    m_date = None  # most recent malignant date

    for episode in client.episodes:
        if None in (episode.id, episode.opened_date):
            continue

        date = episode.opened_date

        if episode.has_malignant_opinions:
            if (m_date is None) or (date > m_date):
                m_date = date
        else:
            if (nm_date is None) or (date < nm_date):
                nm_date = date

        if nm_date and m_date:
            if nm_date < m_date:
                return True

    return False


def filter_studies_by_event_type(
    client: omidb.client.Client, event_type: List[Event], exact_match: bool = True
) -> omidb.client.Client:
    """
    Remove studies (``omidb.study.Study``) from ``client`` whose event type
    includes one or all (if ``exact_match`` is ``True``) of those listed by
    ``event_type``.

    :param client: A classified client with more than one episode
    :param event_type: A list of event types
    :param exact_match: If ``True`` the event types of a study must all of
        those in ``event_type``.
    """

    new_client = copy.deepcopy(client)
    ids = []
    for idx, episode in enumerate(new_client.episodes):
        for study in episode.studies:
            if exact_match and set(study.event_type) != set(event_type):
                ids.append(study.id)
            elif not any([_ in study.event_type for _ in event_type]):
                ids.append(study.id)

    # remove studies
    for ep in new_client.episodes:
        ep.studies = filter(lambda s: s.id != study.id, episode.studies)

    return new_client


def _earliest_date(episode: Episode) -> datetime.date:
    """
    Returns the earliest date from this episodes event dates.

    If no event dates are present, the earliest date is taken as
    ``Episode.diagnosis_date`` for ``Type.CI`` episodes and
    ``Episode.opened_date`` otherwise.
    Raises a ``ValueError`` if no dates are found.
    """

    dates: List[datetime.date] = []
    if episode.events is not None:
        for field in dataclasses.fields(episode.events):
            event = getattr(episode.events, field.name)
            if not event:
                continue
            if isinstance(event, list):
                for e in event:
                    if e.dates is not None:
                        dates += e.dates
            else:
                dates += event.dates if event.dates is not None else []
    if dates:
        return min(dates)
    if episode.type == Type.CI:
        if episode.diagnosis_date is not None:
            return episode.diagnosis_date  # type: ignore
    elif episode.opened_date is not None:
        return episode.opened_date  # type: ignore
    raise ValueError("No valid dates to compare")


def _find_next_episodes(
    episode: Episode,
    all_episodes: List[Episode],
) -> List[Episode]:
    all_episodes = sorted(all_episodes, key=_earliest_date)
    idx = all_episodes.index(episode)
    if idx < len(all_episodes) - 1:
        return all_episodes[idx + 1 :]
    return []


def _find_next_episode(
    episode: Episode,
    all_episodes: List[Episode],
) -> Optional[Episode]:
    all_episodes = sorted(all_episodes, key=_earliest_date)
    idx = all_episodes.index(episode)
    if idx < len(all_episodes) - 1:
        return all_episodes[idx + 1]
    return None


def _within_time_period(e1: Episode, e2: Episode, num_months: int) -> Optional[bool]:
    t1 = _earliest_date(e1)
    t2 = _earliest_date(e2)
    if t2 - t1 <= datetime.timedelta(num_months * 365 / 12):
        return True
    return False


def _is_time_bounded_cancer_prior(
    e1: Episode, e2: Episode, num_months: int = 39
) -> bool:
    test_time = _within_time_period(e1, e2, num_months)
    if test_time and e2.has_malignant_opinions:
        return True
    return False


def _is_time_bounded_ci_prior(
    e1: Episode, e2: Episode, num_months: int = 36
) -> Optional[bool]:
    """
    Returns `True` if the `Episode.is_interval_cancer` evaluates to `True` in
    the episode prior to `episode` and the prior is within 3 years of
    `episode`.
    """
    test_time = _within_time_period(e1, e2, num_months)
    if test_time and e2.type == Type.CI:
        if e2.is_interval_cancer:
            return True
        else:
            return None  # Ambiguous
    return False


def _is_not_cancer(ep: Episode) -> bool:
    if ep.status == Status.CI:
        return False
    if ep.type == Type.CI:
        return False
    if ep.status == Status.M:
        return False
    return True


def is_post_op(episode: Episode, all_episodes: List[Episode]) -> bool:
    """
    Returns `True` if *any* episode in `all_episodes` prior to `episode` is of
    type `Episode.CI` or includes surgery information.
    """
    all_episodes = sorted(all_episodes, key=_earliest_date)
    idx = all_episodes.index(episode)
    for ep in all_episodes[:idx]:
        if (
            ep.events is not None
            and ep.events.surgery is not None
            or ep.type == Type.CI
        ):
            return True
    return False


@enum.unique
class EpisodeOutcome(enum.Enum):
    """
    Summarises the overall outcome of an episode according to the event
    opinions and the episode type of this episode and subsequent episodes.
    """

    CI = "Interval Cancer"
    CIP = "Interval Cancer Prior"
    M = "Malignant"
    MP = "Malignant Prior"
    B = "Benign"
    NAB = "Normal with assessment and biopsy and subsequent episode"
    NA = "Normal with assessment and subsequent episode"
    N = "Normal with subsequent non-cancer episode"


@enum.unique
class UndefinedEpisodeOutcome(enum.Enum):
    """
    When an episode cannot be classified into one of `EpisodeOutcome`, the
    episode is undefined with a reason given by this enum.
    """

    InvalidEvents = "No events or invalidated"
    InvalidFollowUp = "Follow up too early"
    InvalidPrior = "Non-normal found, but CI/MP prior criteria not satisfied"
    InvalidCI = "Event opinions contradict CI episode type"
    DateError = "Episodes cannot be sorted"
    NoSubsequentEpisode = "Subsequent episode not found"


def episode_outcome(
    episode: Episode,
    all_episodes: List[Episode],
    num_months_ci_prior: Optional[int] = None,
    num_months_cancer_prior: Optional[int] = None,
    num_months_normal_follow_up: Optional[int] = None,
    num_months_benign_follow_up: Optional[int] = None,
) -> Tuple[Union[EpisodeOutcome, UndefinedEpisodeOutcome], Optional[str]]:
    """
    Classifies an episode into one of the enumerations defined by
    ``EpisodeOutcome``, or ``UndefinedEpisodeOutcome`` if the classification
    criteria is not satisfied based on logic and/or insufficient data. For
    episodes outcomes that depend directly on a subsequent episode, the ID of
    that episode is returned alongside the outcome.

    :param episode: The episode to classify
    :param all_episodes: All episodes belonging to a single client
    :param num_months_ci_prior: The maximum number of months between an
        interval cancer and *any* previous episode for a previous episode to be
        considered a prior (``EpisodeOutcome.CIP``). If ``None`` (the default) the time
        interval between adjacent episodes is not considered, and the proximal
        prior of the interval cancer qualifies as ``EpisodeOutcome.CIP``, regardless of
        the amount of time between them.
    :param num_months_cancer_prior: The maximum number of months between a
        malignant episode (not an interval cancer) and *any* previous episode for a
        previous episode to be considered a prior (``EpisodeOutcome.MP``). If ``None``
        (the default) the time interval between adjacent episodes is not considered, and
        the proximal prior of the malignant cancer qualifies as ``EpisodeOutcome.MP``,
        regardless of the amount of time between them.
    :param num_months_normal_follow_up: The number of months _after_ which a
        second normal episode must exist in order for ``episode`` to be classified
        as normal. If ``None``, no follow-up is required.
    :param num_months_benign_follow_up: The number of months _after_ which a
        second non-malignant episode must exist in order for ``episode`` to be
        classified as benign. If ``None``, no follow-up is required, which may be
        preferred if the NBSS biopsy opinion is to serve as the ground truth.

    The classification logic is as follows (statuses are presented in order or
    precedence):

    ``EpisodeOutcome.CI``:
        - Episode type is CI; and
        - Episode outcome is malignant or has no surgery/biopsy information
        - If the second condition is not satisfied, status is undefined (``None``)

    ``EpisodeOutcome.M``:
        - Episode outcome is malignant

    ``EpisodeOutcome.CIP``:
        - Episode is the proximal prior of a CI episode occurring within
          ``num_months_ci_prior`` months. If ``num_months_ci_prior`` is
          not ``None``, ``episode`` is considered a prior if it falls within
          the specified time interval.
        - The CI episode must have a malignant outcome or no surgery/biopsy
          information. Otherwise, the prior is undefined (``None``).

    ``EpisodeOutcome.MP``:
        - Episode is the proximal prior of a malignant episode occurring within
          ``num_months_cancer_prior`` months. If ``num_months_ci_prior`` is
          not ``None``, ``episode`` is considered a prior if it falls within
          the specified time interval.

    ``EpisodeOutcome.B``:
        - If ``num_months_benign_follow_up`` is not
          ``None``, there must be a non-cancer after the specified number of
          months, and no cancer before. If ``None`` (the default), there is no
          requirement for a subsequent episode.
        - Episode contains biopsy events, leading to an ``EpisodeStatus`` of ``B``.


    ``EpisodeOutcome.NAB``:
        -  If ``num_months_normal_follow_up`` is not
          ``None``, there must be a non-cancer after the specified number of
          months, and no cancer before. If ``None`` (the default), there is no
          requirement for a subsequent episode.
        - Episode contains assessment and biopsy events.

    ``EpisodeOutcome.NA``:
        - The subsequent episode is not ``EpisodeOutcome.CI`` or
          ``EpisodeOutcome.M``. If ``num_months_normal_follow_up`` is not
          ``None``, there must be a non-cancer after the specified number of
          months, and no cancer before.
        - Episode contains an assessment event.
        - Episode and subsequent episodes' events must be present (not ``None``)

    ``EpisodeOutcome.N``:
        - The subsequent episode is not ``EpisodeOutcome.CI`` or
          ``EpisodeOutcome.M``. If ``num_months_normal_follow_up`` is not
          ``None``, there must be a non-cancer after the specified number of
          months, and no cancer before.
        - Episode and subsequent episode events must be present (not ``None``)


    Notes:
    - For statuses that depend on the input episode and subsequent episode(s),
      these episodes must not have any empty (``None``) left/right opinions
      in any non-screening event (if any).

    - If the above conditions are not satisfied and no ``ValueError``s are
      thrown, the episode type undefined: an ``UndefinedEpisodeOutcome`` is
      returned.

    - With the exception of interval cancers, the ``Type`` of episode is not
      considered when classifying an episode. You should pre-filter the
      episodes by ``Type`` if you would like restrict the classification to
      specific episode types, or otherwise adapt this function as needed.

    See also: ``is_post_op``.
    """
    episode_status = episode.status
    # Cancers
    if episode_status == Status.CI:
        return EpisodeOutcome.CI, None
    if episode.type == Type.CI:
        # Should this be invalidCI?
        return UndefinedEpisodeOutcome.InvalidEvents, None
    if episode_status == Status.M:
        return EpisodeOutcome.M, None

    if episode.events is None or not _validate_events(episode):
        return UndefinedEpisodeOutcome.InvalidEvents, None

    """
    The next group depend on next episode and validated events, which may
    raise exceptions
    """
    try:
        for n_ep in _find_next_episodes(episode, all_episodes):
            if not _validate_events(n_ep):
                return UndefinedEpisodeOutcome.InvalidEvents, None
    except ValueError:
        return UndefinedEpisodeOutcome.DateError, None

    next_episode = _find_next_episode(episode, all_episodes)

    """
    if no follow-up, then we may only classify as normal or benign
    so long as a follow-up is not required. We need to check for
    a subsequent episode because priors trump negatives
    """
    if next_episode is None:
        if num_months_benign_follow_up is None:
            if episode_status == Status.B:
                return EpisodeOutcome.B, None

        if num_months_normal_follow_up is None:
            return _classify_normal_or_raise(episode), None

        return UndefinedEpisodeOutcome.NoSubsequentEpisode, None

    if num_months_ci_prior is None:
        num_months_ci_prior = ceil(
            12 * (_earliest_date(next_episode) - _earliest_date(episode)).days / 365.0
        )

    if num_months_cancer_prior is None:
        num_months_cancer_prior = ceil(
            12 * (_earliest_date(next_episode) - _earliest_date(episode)).days / 365.0
        )

    longest_window = max(num_months_ci_prior or 0, num_months_cancer_prior or 0)

    for n_ep in _find_next_episodes(episode, all_episodes):
        if _within_time_period(episode, n_ep, longest_window):
            if n_ep.type == Type.CI:
                res = _classify_ci_prior(episode, n_ep, num_months_ci_prior)
                if res:
                    return EpisodeOutcome.CIP, n_ep.id
                elif res is None:
                    return UndefinedEpisodeOutcome.InvalidEvents, n_ep.id
                else:
                    return UndefinedEpisodeOutcome.InvalidPrior, n_ep.id
            elif n_ep.status == Status.M:
                res = _classify_m_prior(episode, n_ep, num_months_cancer_prior)
                if res:
                    return EpisodeOutcome.MP, n_ep.id
                else:
                    return UndefinedEpisodeOutcome.InvalidPrior, n_ep.id
        else:
            break

    """
    Here we check if a follow-up is required or not.
    If not, then early return benign or normal.
    Otherwise, continue using the approproate number of months
    as the minimum inter-episode time delta.
    """
    if episode_status == Status.B:
        if num_months_benign_follow_up is None:
            return EpisodeOutcome.B, None
        num_months = num_months_benign_follow_up
    else:
        if num_months_normal_follow_up is None:
            return _classify_normal_or_raise(episode), None
        num_months = num_months_normal_follow_up

    """
    A follow-up is required.
    `episode_to_check` is either the first
    episode AFTER the `num_months_normal_follow_up` or `None`.
    If `None` then we assume we have no valid follow-up.
    """
    episode_to_check = None

    for ep in _find_next_episodes(episode, all_episodes):
        if ep.events is None:
            return UndefinedEpisodeOutcome.InvalidEvents, ep.id
        # is there a cancer inside window?
        if _within_time_period(episode, ep, num_months):
            if not _is_not_cancer(ep):
                return UndefinedEpisodeOutcome.InvalidPrior, ep.id
        # first episode outside window
        else:
            episode_to_check = ep
            break

    if episode_to_check is None:
        return UndefinedEpisodeOutcome.InvalidFollowUp, None

    # first episode outside window is cancer, so must be invalid prior
    if not _is_not_cancer(episode_to_check):
        return UndefinedEpisodeOutcome.InvalidPrior, episode_to_check.id

    # At this point we have two non-malignant neighbouring episodes
    if episode_status == Status.B:
        return EpisodeOutcome.B, episode_to_check.id

    return _classify_normal_or_raise(episode), episode_to_check.id


def _classify_normal_or_raise(episode: Episode) -> EpisodeOutcome:
    normal = _classify_normal(episode.status)
    if normal is None:
        raise ValueError(
            f"Failed to classify episode {episode.id}, unexpected condition"
        )
    return normal


def _classify_normal(s: Optional[Status]) -> Optional[EpisodeOutcome]:
    if s == Status.NAB:
        return EpisodeOutcome.NAB
    if s == Status.NA:
        return EpisodeOutcome.NA
    if s == Status.N:
        return EpisodeOutcome.N
    return None


def _classify_prior(
    episode: Episode,
    next_episode: Episode,
    num_months_ci_prior: Optional[int],
    num_months_cancer_prior: Optional[int],
) -> Optional[bool]:
    if next_episode.type == Type.CI:
        return _classify_ci_prior(episode, next_episode, num_months_ci_prior)
    else:
        return _classify_m_prior(episode, next_episode, num_months_ci_prior)


def _classify_ci_prior(
    episode: Episode, next_episode: Episode, num_months_ci_prior: Optional[int]
) -> Optional[bool]:
    if next_episode.type == Type.CI:
        if num_months_ci_prior is not None:
            is_valid_ci_prior = _is_time_bounded_ci_prior(
                episode, next_episode, num_months_ci_prior
            )
        elif next_episode.is_interval_cancer:
            is_valid_ci_prior = True
        else:
            is_valid_ci_prior = None

        if is_valid_ci_prior:
            return True
        elif is_valid_ci_prior is None:
            return None
    return False


def _classify_m_prior(
    episode: Episode, next_episode: Episode, num_months_cancer_prior: Optional[int]
) -> bool:
    if (next_episode.type != Type.CI) and next_episode.has_malignant_opinions:
        if num_months_cancer_prior is None or _is_time_bounded_cancer_prior(
            episode, next_episode, num_months_cancer_prior
        ):
            return True
    return False
