from dataclasses import dataclass
import enum
from typing import List
from . import episode


@enum.unique
class Status(enum.Enum):
    """
    Summarises the overall status of a client according to the event opinions
    within an episode, and the type of episode itself.
    """

    B = "Benign"
    M = "Malignant"
    N = "Normal"
    CI = "Interval Cancer"


@dataclass
class Client:
    """
    A client represents a patient who has attended the NHS screening programme.

    Each client will have one or more :class:`omidb.episode.Episode` s, for
    which (anonymised and pseudonymised) NBSS information can be found.

    :param id: Client identifier, typically a four letter ID followed by a
        series of digits, e.g. `optm1`, `demd7050`
    :param episodes: A list of :class:`omidb.episode.Episode` s associated with
        the client
    :param site: code denoting the clinical site/centre where screening took
        place
    """

    id: str
    episodes: List[episode.Episode]
    site: str

    @property
    def status(self) -> Status:
        """
        Determines the :class:`omidb.client.Status` by first classifying
        each episode according to its type and the surgery and biopsy opinions,
        and subsequently applying the following precedence rules
        (from top to bottom: highest to lowest precedence):

        - :class:`Status.CI`: if any interval cancer episode

        - :class:`Status.M`: if any malignant episode (based on surgery/biopsy opinions)

        - :class:`Status.B`: if any benign episode (based on surgery/biopsy opinions)

        - :class:`Status.N`: otherwise
        """

        for ep in self.episodes:
            if ep.type == episode.Type.CI:
                return Status.CI

        for ep in self.episodes:
            if ep.has_malignant_opinions:
                return Status.M

        for ep in self.episodes:
            if ep.has_benign_opinions:
                return Status.B

        return Status.N
