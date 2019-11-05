#!/usr/bin/env python3
from typing import Generator, Tuple, Dict, Any, List
import regex as requests
import regex as re

from katana.repl.ctf import CTFProvider, Challenge, User, AuthenticationError, Bracket


class Provider(CTFProvider):
    def __init__(self, *args, **kwargs):
        self.session: requests.Session = None
        self.token: str = None

        super(Provider, self).__init__(*args, **kwargs)

    def _api(
        self,
        endpoint: str,
        args: Dict[str, Any] = {},
        params: Dict[str, str] = {},
        method="GET",
        recurse=True,
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
            params=params,
            headers={"X-CSRF-Token": self.token},
        )

        # If we are redirected, then it is likely due to an authentication error
        # We allow a single authentication re-attempt.
        if r.status_code == 302 and recurse:
            # Attempt re-auth
            self._authenticate(self.username, self.password)
            # Retry API call
            return self._api(endpoint, args, params, method, recurse=False)

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

        # Request the user profile
        success, result, _ = self._api("/user")
        if not success:
            return None

        self.me = User(result["username"], result["score"], result["tid"])

        # Grab the team information
        success, team, _ = self._api("/team")
        if not success:
            return

        # Grab brackets
        brackets = self.brackets

        for b in brackets:
            if b.ident == team["eligibilities"][0]:
                self.me.bracket = b

        # Save team name
        self.me.team = team["team_name"]

    @property
    def brackets(self) -> List[Bracket]:

        # Request a list of scoreboards (brackets)
        success, result, resp = self._api("/scoreboards")
        if not success:
            return []

        # We want brackets with higher priority first
        result.sort(key=lambda b: b["priority"], reverse=True)

        # Build bracket list
        brackets: List[Bracket] = [Bracket(b["name"], b["sid"]) for b in result]

        return brackets

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
    def users(self) -> Generator[User, None, None]:
        """ This is difficult for picoCTF. We are not going to implement it right now... """
        return

    def scoreboard(
        self, localize: User = None, count=10, bracket: Bracket = None
    ) -> Dict[int, User]:

        # Pico lists the scoreboard around your user by default
        if localize is not None:
            params = {}
        else:
            params = {"page": 1}

        if bracket is None and localize is not None:
            # Use this user's bracket
            bracket = localize.bracket
        elif bracket is None:
            # Default to the highest priority bracket
            bracket = self.brackets[0]

        # Grab the scoreboard
        success, board, _ = self._api(
            f"/scoreboards/{bracket.ident}/scoreboard", params=params
        )
        if not success:
            return []

        # Calculate start based on localize
        if localize is not None:
            pos = 0
            for n, team in enumerate(board["scoreboard"]):
                if team["name"] == localize.team:
                    pos = n
            start = pos - int(count / 2)
        else:
            start = 0

        # Calculate end from start and count
        end = start + count

        # Bound start and end within the results
        if start < 0:
            end -= start
            start = 0
        if end > len(board["scoreboard"]):
            start -= end - len(board["scoreboard"])
            end = len(board["scoreboard"])
        if start < 0:
            start = 0

        return {
            ((board["current_page"] - 1) * 50 + n + 1): User(
                t["name"], t["score"], None, t["name"], [], bracket
            )
            for n, t in enumerate(board["scoreboard"][start:end])
        }

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
