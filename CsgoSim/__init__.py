from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
import random as r
from typing import Dict, Generator, List

import yaml


class _DictClass:
    def __init__(self, config: Dict):
        for key, value in config.items():
            self.__dict__[key] = value


@dataclass(init=False)
class _Weapon(_DictClass):
    name: str
    price: int = -1
    award: int = -1
    damage: int = -1
    penetration: float = -1

    def __init__(self, config: Dict, name: str):
        super().__init__(config)

        self.name = name


@dataclass(init=False)
class _Equipment(_DictClass):
    name: str
    price: int = -1
    price_damaged: int = -1

    def __init__(self, config: Dict, name: str):
        super().__init__(config)

        self.name = name


class Side(Enum):
    CT = auto
    T = auto


class Role(Enum):
    AWP = auto
    RIFLE = auto


@dataclass(init=False)
class _Player(_DictClass):
    primary: _Weapon = None
    secondary: _Weapon = None
    grenades: List[_Equipment] = None
    default_secondary: _Weapon = None
    kit: _Equipment = None
    money: int = 0
    armor: int = 0
    helmet: bool = False
    health: int = 100
    side: Side = None
    role: Role = Role.RIFLE

    def __init__(self, config: Dict, weapons: Dict[str, Dict[str, _Weapon]]):
        super().__init__(config)
        if self.side == "t":
            self.default_secondary = weapons["pistols"]["glock"]
        else:
            self.default_secondary = weapons["pistols"][r.choice(("usps", "p2000"))]

    def buy_item(self):
        pass


class Simulation:
    def __init__(self, config_path: Path = "config"):
        if isinstance(config_path, str):
            self._config_path = Path(config_path)
        else:
            self._config_path = config_path
        with open(self._config_path / Path("config.yaml")) as config_file:
            self._config = yaml.safe_load(config_file)

        if self._config["random_seed"] != 0:
            r.seed(self._config["random_seed"])

        self.t: List[_Player] = []
        self.ct: List[_Player] = []
        self.weapons: Dict[str, Dict[str, _Weapon]] = {}
        self.equipment: Dict[str, Dict[str, _Equipment]] = {}
        self.round_num = 0

        for class_, weapons in self._config["weapons"].items():
            self.weapons[class_] = {name: _Weapon(data, name) for name, data in weapons.items()}

        for class_, equipment in self._config["equipment"].items():
            self.equipment[class_] = {name: _Equipment(data, name) for name, data in equipment.items()}

    def start(self):
        self._reset_gamestate()

        # Assign roles
        for p in r.sample(self.t, self._config["roles"]["awp"]):
            p.role = Role.AWP
        for p in r.sample(self.ct, self._config["roles"]["awp"]):
            p.role = Role.AWP

        for round_num in range(self._config["rounds"]):
            self._sim_round()
            self.round_num = round_num

    def _sim_round(self):
        self._buy_period()
        self._early_round()
        self._mid_round()
        self._late_round()

    def _buy_period(self):
        # Pistol round
        if self.round_num in (0, self._config["rounds"] / 2):
            for player in self._players():
                player.money = self._config["economy"]["starting_money"]
                player.secondary = player.default_secondary
                self._process_purchases(player, self._config["buy_settings"]["pistol_round"]["purchase_priorities"])

    def _process_purchases(self, player: _Player, priorities: List):
        for entry in priorities:
            if isinstance(entry, str) or len(entry) == 1:
                pass  # TODO Figure out how to actually do the purchasing
            else:
                if isinstance(entry[0], dict) and entry[0].get("p"):  # Assume entry is a weighted probability list
                    choice = r.choices(entry, weights=[e["p"] for e in entry], k=1)
                else:
                    choice = r.choice(entry)
                if isinstance(choice, str):
                    pass


    def _reset_gamestate(self):
        self.round_num = 0
        self.t = [_Player({"side": Side.T}, self.weapons) for _ in range(5)]
        self.ct = [_Player({"side": Side.CT}, self.weapons) for _ in range(5)]

    def _players(self) -> Generator[_Player, None, None]:
        for player in self.t:
            yield player

        for player in self.ct:
            yield player
