import random as r
from typing import Dict, List, Union


def choice_helper(choice: Union[List, Dict, str], side: str):
    if isinstance(choice, str):
        return choice
    elif isinstance(choice, list):
        if len(choice) == 0:
            return
        if isinstance(choice[0], dict):  # choice is a weighted list
            choice = r.choices(choice, weights=[e["p"] for e in choice], k=1)[0]
        else:  # choice is a list of strings (evenly weighted)
            choice = r.choice(choice)
    elif isinstance(choice, dict):
        try:
            # Will succeed if choice contains a team-based sub-list
            choice = choice["t"] if side == "t" else choice["ct"]
        except KeyError:
            try:
                # Will succeed if choice contains a non-team-based sub-list
                choice = choice["c"]
            except KeyError:
                # At this point choice must be a weighted string, with no sub-list
                choice = choice["n"]
    return choice_helper(choice, side)
