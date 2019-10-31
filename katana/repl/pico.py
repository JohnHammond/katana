#!/usr/bin/env python3
from typing import Generator, Tuple, Dict, Any, List
import requests
import re

from katana.repl.ctf import CTFProvider, Challenge, User, AuthenticationError


class Provider(CTFProvider):
    def __init__(self, *args, **kwargs):
        self.session: requests.Session = None
        self.token: str = None

        super(Provider, self).__init__(*args, **kwargs)

    def _api(
        self, endpoint: str, args: Dict[str, Any] = {}, method="GET", recurse=True
    ) -> Tuple[bool, Dict[str, Any], requests.Response]:
        """
        Perform an API request to the specified endpoint
        :param endpoint: the endpoint to query (e.g. /user/login)
        :param args: Arguments (e.g. {'username': 'user', 'password': 'password'})
        :param method: Either POST or GET
        :return: A tuple containing (success: bool, response: dict)
        """
        if self.session is None:
            self.session = requests.Session()

        # Lookup table for methods
        methods = {"GET": self.session.get, "POST": self.session.post}

        # Ensure valid method
        if method.upper() not in methods:
            return False, {}, None

        endpoint = endpoint.lstrip("/")

        # Perform the request
        r = methods[method](
            f"{self.url}/api/v1/{endpoint}",
            json=args,
            headers={"X-CSRF-Token": self.token},
        )

        # If we are redirected, then it is likely due to an authentication error
        # We allow a single authentication re-attempt.
        if r.status_code == 302 and recurse:
            # Attempt re-auth
            self._authenticate(self.username, self.password)
            # Retry API call
            return self._api(endpoint, args, method, recurse=False)

        # Ensure we are good to go
        if r.status_code != 200:
            return False, {}, r

        # Return the response
        return True, r.json(), r

    def _authenticate(self, username: str, password: str) -> None:

        # Build session
        self.session = requests.Session()

        # Attempt authentication
        success, result, resp = self._api(
            "/user/login",
            args={"username": username, "password": password},
            method="POST",
        )

        # Check if we succeeded
        if not success or not result["success"]:
            raise AuthenticationError()

        # Save CSRF token
        self.token = resp.cookies["token"]

    @property
    def challenges(self) -> Generator[Challenge, None, None]:

        # Request problem list
        success, result, _ = self._api("/problems")

        # Ensure we got something back
        if not success:
            return

        for c in result:
            yield self._parse_challenge(c)

        return

    @property
    def me(self) -> User:

        # Request the user profile
        success, result, _ = self._api("/user")
        if not success:
            return None

        return User(result["username"], result["score"], result["tid"])

    @property
    def users(self) -> Generator[User, None, None]:
        """ This is difficult for picoCTF. We are not going to implement it right now... """
        return

    def get_challenge(self, ident: str) -> Challenge:

        success, result, _ = self._api(f"/problems/{ident}")
        if not success:
            return None

        return self._parse_challenge(result)

    def _parse_challenge(self, result) -> Challenge:
        """
        Parse the result of a challenge/problem request (either from /problem or from a specific problem)
        :param result: The result dictionary from the API call
        :return: A new challenge instance
        """

        file_pattern = re.compile(r"href='(//[^/]+/static/[^']+)'>")
        matches: List[Tuple[str, str]] = file_pattern.findall(result["description"])

        method = "http"
        if "://" in self.url:
            method = self.url.split(":")[0]

        files = {}
        if matches is not None:
            files = {match.split("/")[-1]: f"{method}:{match}" for match in matches}

        return Challenge(
            result["name"],
            result["score"],
            result["pid"],
            self,
            result["description"],
            files,
            [result["category"]],
            result["solved"],
        )

    def submit(self, challenge: Challenge, flag: str) -> Tuple[bool, int]:

        # Make the submission request
        success, result, _ = self._api(
            "/submissions",
            args={"key": flag, "method": "api", "pid": challenge.ident},
            method="POST",
        )
        if not success:
            return False, -1

        return result["correct"], -1
