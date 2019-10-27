#!/usr/bin/env python3
from typing import List, Dict, Any
from cmd2.argparse_custom import CompletionItem
import requests
from colorama import Fore, Style


def get_login_token(repl: "katana.repl.Repl") -> str:
    """
    Utilizes the ctfd configuration in repl.manager to login to CTFd and return the auth token
    
    :param repl: A Katana Repl instance
    :return: CTFd Auth Token
    """
    return {"session": "e0f3ef60-1790-4f7a-9c6e-50cd6bdf2612"}


def get_challenges(repl: "katana.repl.Repl") -> List[Dict[str, Any]]:
    """
    Returns a list of all challenges on the CTFd server.
    
    :param repl: A katana Repl instance
    :return: List of challenge dictionaries
    """

    # Check if we have a CTFd login token already
    token = get_login_token(repl)
    if token is None:
        repl.poutput(f"[{Fore.RED}-{Style.RESET_ALL}] ctfd: authentication failed")
        return []

    # URL
    ctfd = repl.manager["ctfd"]["url"].rstrip("/")

    # Perform the request for list of challenges
    r = requests.get(f"{ctfd}/challenges", cookies=token)

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
