#!/usr/bin/env python3
from typing import Generator, List, Dict, Any, Tuple
from dataclasses import dataclass, field
import importlib


@dataclass
class Challenge:
    """ A CTF Challenge """

    title: str
    value: int
    ident: int
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


class AuthenticationError(Exception):
    """ Indicates a failure to authenticate with the CTF """

    pass


class CTFProvider(object):
    """ Provides an interface into a remote CTF platform """

    def __init__(self, url: str, username: str, password: str):
        super(CTFProvider, self).__init__()

        # Store parameters
        self.url = url
        self.username = username
        self.password = password

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
    def me(self) -> User:
        """ Returns a user representing the currently logged in user """
        return None

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
    if provider not in known_providers:
        raise ValueError(f"{provider}: not in known providers: {repr(known_providers)}")

    # Import the provider module
    module = importlib.import_module(f"katana.repl.{provider}")

    # Create the provider object
    provider: CTFProvider = module.Provider(url, username, password)

    # Return the new object
    return provider
