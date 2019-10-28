#!/usr/bin/env python3
from typing import List, Dict, Any
from cmd2.argparse_custom import CompletionItem
import requests
from colorama import Fore, Style


def get_login_token(repl: "katana.repl.Repl") -> requests.Session:
    """
    Utilizes the ctfd configuration in repl.manager to login to CTFd and return the auth token
    
    :param repl: A Katana Repl instance
    :return: CTFd Auth Token
    """

    # Speed up processing in the future by caching the session
    if repl.ctfd_session is not None:
        return repl.ctfd_session

    # We need CTFd configuration
    if "ctfd" not in repl.manager:
        repl.poutput(f"[{Fore.RED}-{Style.RESET_ALL}] ctfd: no configuration provided")
        return None

    # We also need the URL
    if "url" not in repl.manager["ctfd"]:
        repl.poutput(f"[{Fore.RED}-{Style.RESET_ALL}] ctfd: no url provided")
        return None

    # We also either need a username and password or an auth token
    if (
        not ("username" in repl.manager["ctfd"] and "password" in repl.manager["ctfd"])
        and "session" not in repl.manager["ctfd"]
    ):
        repl.poutput(f"[{Fore.RED}-{Style.RESET_ALL}] ctfd: no authentication provided")
        return None

    # The user specified a session cookie. Just use that (DON'T LOGOUT PLZ)
    if "session" in repl.manager["ctfd"]:
        s = requests.Session()
        s.cookies["session"] = repl.manager["ctfd"]["session"]
        repl.ctfd_session = s
        return s

    # I'm not sure if there is a /api endpoint for this, so I'm using the regular
    # login submission form... :(

    s = requests.Session()

    # Grab the nonce
    r = s.get(f"{repl.manager['ctfd']['url'].rstrip('/')}/login")

    # Bad URL?
    if r.status_code != 200:
        repl.poutput(
            f"[{Fore.RED}-{Style.RESET_ALL}] ctfd: unable to get nonce. bad url?"
        )
        return None

    # Parse nonce from HTML response
    nonce = r.text.split('name="nonce" value="')[1].split('"')[0]

    # Perform authentication
    r = s.post(
        f"{repl.manager['ctfd']['url'].rstrip('/')}/login",
        data={
            "name": repl.manager["ctfd"]["username"],
            "password": repl.manager["ctfd"]["password"],
            "nonce": nonce,
        },
    )

    # Bad credentials?
    if r.status_code != 200:
        repl.poutput(f"[{Fore.RED}-{Style.RESET_ALL}] ctfd: authentication failed")
        return None

    repl.ctfd_session = s

    return s


def get_solves(repl, force: bool) -> List[Dict[str, Any]]:
    """
    Retrieve a list our solves
    
    :param repl: A katana Repl object
    :param force: Force reload from server
    :return: List of solves from the API
    """

    if repl.ctfd_solves is None or force:

        # Check if we have a CTFd login token already
        session = get_login_token(repl)
        if session is None:
            return []

        # URL
        ctfd = repl.manager["ctfd"]["url"].rstrip("/")

        # Perform the request for list of challenges
        r = session.get(f"{ctfd}/api/v1/users/me/solves")

        # Ensure everything is okay
        if r.status_code != 200:
            repl.poutput(
                f"[{Fore.RED}-{Style.RESET_ALL}] ctfd: failed to get solves: {r.status_code}"
            )
            return []

        # Grab the JSON data
        data = r.json()

        # Ensure everything is okay
        if not data["success"]:
            repl.poutput(f"[{Fore.RED}-{Style.RESET_ALL} ctfd: failed to get solves")
            return []

        # Cache challenge list
        repl.ctfd_solves = data["data"]

    return repl.ctfd_solves


def get_challenges(
    repl: "katana.repl.Repl", force: bool = False, solves: bool = False
) -> List[Dict[str, Any]]:
    """
    Returns a list of all challenges on the CTFd server.
    
    :param repl: A katana Repl instance
    :param force: Force a refetch of challenges
    :return: List of challenge dictionaries
    """

    # Cache the challenge list. It shouldn't change, and it makes tab-completions faster.
    if repl.ctfd_challenges is None or force:

        # Check if we have a CTFd login token already
        session = get_login_token(repl)
        if session is None:
            return []

        # URL
        ctfd = repl.manager["ctfd"]["url"].rstrip("/")

        # Perform the request for list of challenges
        r = session.get(f"{ctfd}/api/v1/challenges")

        # Ensure everything is okay
        if r.status_code != 200:
            repl.poutput(
                f"[{Fore.RED}-{Style.RESET_ALL}] ctfd: failed to get challenges: {r.status_code}"
            )
            return []

        # Grab the JSON data
        data = r.json()

        # Ensure everything is okay
        if not data["success"]:
            repl.poutput(
                f"[{Fore.RED}-{Style.RESET_ALL} ctfd: failed to get challenges"
            )
            return []

        # Perform request for list of solves for this user
        r = session.get(f"{ctfd}/api/v1/users/me/solves")

        # Get list of solves
        solves = get_solves(repl, force)

        # Add a 'solved' attribute
        for c in data["data"]:
            challenge_solves = [s for s in solves if s["challenge_id"] == c["id"]]
            if len(challenge_solves) > 0:
                c["solved"] = True
            else:
                c["solved"] = False

        # Cache challenge list
        repl.ctfd_challenges = data["data"]

    return repl.ctfd_challenges


def get_challenge(repl: "katana.repl.Repl", challenge_id: int) -> Dict[str, Any]:
    """
    Grab challenge details for the specified ID
    
    :param repl: The Katana Repl object
    :param challenge_id: The challenge ID
    :return: Dictionary of challenge details
    """

    # Grab a login session
    session = get_login_token(repl)
    if session is None:
        return None

    # Grab challenge
    r = session.get(
        f"{repl.manager['ctfd']['url'].rstrip('/')}/api/v1/challenges/{challenge_id}"
    )

    # Ensure everything is okay
    if r.status_code != 200:
        repl.poutput(
            f"[{Fore.RED}-{Style.RESET_ALL}] ctfd: failed to retrieve challenge"
        )
        return None

    response = r.json()

    # Ensure everything is okay
    if not response["success"]:
        repl.poutput(
            f"[{Fore.RED}-{Style.RESET_ALL}] ctfd: failed to retrieve challenge"
        )
        return None

    # Check if we have solved this
    r = session.get(
        f"{repl.manager['ctfd']['url'].rstrip('/')}/api/v1/challenges/{challenge_id}/solves"
    )

    # Ensure everything is okay
    if r.status_code != 200:
        return response["data"]

    solves = r.json()

    # Ensure everything is okay
    if not solves["success"]:
        return response["data"]

    response["data"]["solves"] = solves["data"]
    response["data"]["solved"] = (
        len(
            [s for s in solves["data"] if s["name"] == repl.manager["ctfd"]["username"]]
        )
        > 0
    )

    # Return the challenge data
    return response["data"]


def get_challenge_choices(repl: "katana.repl.Repl") -> List[CompletionItem]:
    """
    Get a list challenge IDs and titles from the CTFd instance specified in the manager configuration
    
    :param repl:
    :return: List of completion items
    """

    return [
        CompletionItem(c["id"], f"{c['name']} - {c['value']} points")
        for c in get_challenges(repl)
    ]


def submit_flag(
    repl: "katana.repl.Repl", challenge_id: int, flag: str
) -> Dict[str, Any]:
    """
    Attempt to submit a flag.
    
    :param repl: a katana Repl object
    :param challenge_id: the challenge ID to submit to
    :param flag: the flag to submit
    :return: API response dict
    """

    # Login
    session = get_login_token(repl)
    if session is None:
        return None

    url = repl.manager["ctfd"]["url"].rstrip("/")

    # Grab the CSRF token
    r = session.get(url)
    token = r.text.split('csrf_nonce = "')[1].split('"')[0]

    # Attempt submission
    r = session.post(
        f"{url}/api/v1/challenges/attempt",
        json={"challenge_id": challenge_id, "submission": flag},
        headers={"CSRF-Token": token},
    )

    # Is everything okay?
    if r.status_code != 200:
        repl.poutput(
            f"[{Fore.RED}-{Style.RESET_ALL}] ctfd: failed to submit flag: {r.status_code}"
        )
        return None

    response = r.json()

    # Bro, seriously, is everything okay?
    if not response["success"]:
        repl.poutput(f"[{Fore.RED}-{Style.RESET_ALL}] ctfd: failed to submit flag")
        return None

    return response["data"]
