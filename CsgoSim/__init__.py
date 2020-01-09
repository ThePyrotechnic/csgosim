from dataclasses import dataclass, field
import itertools
from pathlib import Path
import random as r
from typing import Dict, List, Tuple

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
    price: int = -1
    price_damaged: int = -1


@dataclass(init=False)
class _Player(_DictClass):
    primary: _Weapon = None
    secondary: _Weapon = None
    grenades: List[_Equipment] = None
    default_secondary: _Weapon = None
    money: int = 0
    armor: int = 0
    helmet: bool = False
    health: int = 100
    side: str = None

    def __init__(self, config: Dict, weapons: Dict[str, Dict[str, _Weapon]]):
        super().__init__(config)
        if self.side == "t":
            self.default_secondary = weapons["pistols"]["glock"]
        else:
            self.default_secondary = weapons["pistols"][r.choice(("usps", "p2000"))]

        self.secondary = self.default_secondary


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

        self.players: List[_Player] = []
        self.weapons: Dict[str, Dict[str, _Weapon]] = {}
        self.equipment: Dict[str, Dict[str, _Equipment]] = {}

        for class_, weapons in self._config["weapons"].items():
            self.weapons[class_] = {name: _Weapon(data, name) for name, data in weapons.items()}

        for class_, equipment in self._config["equipment"].items():
            self.equipment[class_] = {name: _Equipment(data) for name, data in equipment.items()}

    def start(self):
        self._reset_gamestate()

        print(self.players)

    def _reset_gamestate(self):
        self.players = [_Player({"side": "t"}, self.weapons) for _ in range(5)]
        self.players.extend([_Player({"side": "ct"}, self.weapons) for _ in range(5)])

