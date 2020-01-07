import json
from dataclasses import dataclass


@dataclass
class Simulation:
    games: int

    def __init__(self):
        with open("config.json") as config_file:
            self.__dict__ = json.load(config_file)

    def start(self):
        for game_num in range(self.games):
            print(game_num)