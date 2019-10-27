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

    return s


def get_challenges(repl: "katana.repl.Repl") -> List[Dict[str, Any]]:
    """
    Returns a list of all challenges on the CTFd server.
    
    :param repl: A katana Repl instance
    :return: List of challenge dictionaries
    """

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
        repl.poutput(f"[{Fore.RED}-{Style.RESET_ALL} ctfd: failed to get challenges")
        return []

    return data["data"]


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
