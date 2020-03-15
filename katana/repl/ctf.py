#!/usr/bin/env python3
from typing import Generator, List, Dict, Any, Tuple
from dataclasses import dataclass, field
import importlib


@dataclass
class Challenge:
    """ A CTF Challenge """

    title: str
    value: int
    ident: str
    provider: "CTFProvider"
    description: str = None
    files: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    solved: bool = False


@dataclass
class User:
    """ A user in the CTF game. Not all fields may be filled. """

    name: str
    score: int
    ident: str
    team: str = None
    solves: List[Challenge] = field(default_factory=list)
    bracket: "Bracket" = None


@dataclass
class Bracket:
    """ A bracket is a specific group of users you play against. PicoCTF calls them
    "scoreboards". Most CTFs don't implement this, though. """

    name: str
    ident: str


class AuthenticationError(Exception):
    """ Indicates a failure to authenticate with the CTF """

    pass


class CTFProvider(object):
    """ Provides an interface into a remote CTF platform """

    def __init__(self, url: str, username: str, password: str, api_version: str):
        super(CTFProvider, self).__init__()

        # Store parameters
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self.api_version = api_version
        self.me: User = None

        # Authenticate and retrieve self user
        self._authenticate(username, password)

    @property
    def challenges(self) -> Generator[Challenge, None, None]:
        """
        Returns a Generator yielding visible challenges. Only name, value, and ident are guaranteed.
        In order to retrieve all challenge properties, use `get_challenge` with the returned ident.
        
        :return: Generator of challenges
        """
        return

    @property
    def users(self) -> Generator[User, None, None]:
        """ Returns a Generator yielding Users from highest score to lowest """
        return

    @property
    def brackets(self) -> List[Bracket]:
        """ Return a list of brackets for this CTF. If a provider doesn't use brackets
         this function will simply return a single "DEFAULT" bracket """
        return [Bracket(name="default", ident="default")]

    def scoreboard(
        self, localize: User = None, count=10, bracket: Bracket = None
    ) -> Dict[int, User]:
        """
        Returns a list of users referring to the current scoreboard
        :param bracket: which bracket to query
        :param localize: Name of a user to localize results around (or None)
        :param count: Number of results to return
        :return: Dictionary of mapping scoreboard position to user
        """

        # NOTES: PicoCTF supports multiple scoreboards/brackets. I'm not sure how to support this.
        # We can return the "default" scoreboard here, but that may not be right. Really, the
        # CTFProvider class should support a "bracket" or "scoreboard" option, which would be
        # "DEFAULT" or something for things like CTFd, but used for PicoCTF. After that, we can
        # search for the team name, and return results relevant to the team we specify under the
        # specified bracket. This requires a way to list brackets as well, which is also not
        # supported at the moment. These are all abstractions that need to be implemented for Pico
        # that would hold default/stub methods for simpler platforms like CTFd. I need to think about
        # the interface more before committing to an implementation. For now, the scoreboard will
        # simply be empty for PicoCTF, which doesn't break anything but is disappointing. :(

        return {}

    def get_challenge(self, ident: str) -> Challenge:
        """
        Query the entire challenge by identifier
        
        :param ident: An integer identifier (likely retrieved from self.challenges)
        :return: Challenge object with all details filled
        """

        return None

    def submit(self, challenge: Challenge, flag: str) -> Tuple[bool, int]:
        """
        Attempt to submit a flag to the CTF server for the specified challenge.
        
        :param challenge: The challenge for which you are submitting a flag
        :param flag: The flag to submit
        :return: A tuple containing (success: bool, attempts_left: int)
        """
        return False, 0

    def _authenticate(self, username: str, password: str) -> None:
        """
        Authenticate with the remote CTF instance. Raise AuthenticationError on failure.
        
        :param username: A valid username
        :param password: The cooresponding password
        :return: A user object representing the user we authenticated as
        """
        raise AuthenticationError("Not implemented")


def get_provider(provider: str, url: str, username: str, password: str) -> CTFProvider:
    """
    Build a CTFProvider object for the specified CTF provider name. The provider must
    be one of the known implemented CTF Providers. If it is not, a ValueError is raised.
    If the credentials are incorrect or we cannot connect to the CTF, an AuthenticationError
    is raised.
    
    :param provider: The provider name (e.g. "ctfd")
    :param url: The CTF URL
    :param username: A valid username
    :param password: A valid password
    :return: An initialized CTFProvider object
    """

    # Ensure this is an allowed provider
    known_providers = ["ctfd", "pico"]

    # Split provider from api version
    provider = provider.split("-")
    if len(provider) == 1:
        provider = provider[0]
        api_version = None
    else:
        api_version = "-".join(provider[1:])
        provider = provider[0]

    if provider not in known_providers:
        raise ValueError(f"{provider}: not in known providers: {repr(known_providers)}")

    # Import the provider module
    module = importlib.import_module(f"katana.repl.{provider}")

    # Create the provider object
    provider: CTFProvider = module.Provider(url, username, password, api_version)

    # Return the new object
    return provider
