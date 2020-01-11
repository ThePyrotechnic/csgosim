from collections import defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
import random as r
from typing import Dict, Generator, List, Union

import yaml


class _DictClass:
    def __init__(self, config: Dict):
        for key, value in config.items():
            self.__dict__[key] = value


@dataclass(init=False)
class _Buyable(_DictClass):
    name: str
    type_: str
    price: int = -1

    def __init__(self, config: Dict, type_: str, name: str):
        super().__init__(config)

        self.name = name
        self.type_ = type_


@dataclass(init=False)
class _Weapon(_Buyable):
    award: int = -1
    damage: int = -1
    penetration: float = -1


@dataclass(init=False)
class _Equipment(_Buyable):
    price_damaged: int = -1
    limit: int = -1


@dataclass(init=False)
class _Player(_DictClass):
    primary: _Weapon = None
    secondary: _Weapon = None
    grenades: List[_Equipment] = None
    default_secondary: _Weapon = None
    limits: defaultdict = None
    money: int = 0
    armor: int = 0
    helmet: bool = False
    kit: bool = False
    health: int = 100
    side: str = None
    role: str = "rifle"
    position: str = None

    def __init__(self, config: Dict, default_secondary: Union[List, str]):
        super().__init__(config)
        if isinstance(default_secondary, list):
            self.default_secondary = Simulation.items[r.choice(default_secondary)]
        else:
            self.default_secondary = Simulation.items[default_secondary]

        self.grenades = []
        self.limits = defaultdict(int)

    def process_purchases(self, priorities: Dict[str, List]):
        def _purchase_helper(choice: Union[List, Dict, str]):
            if isinstance(choice, str):
                self.buy_item(choice)
                return
            elif isinstance(choice, list):
                if isinstance(choice[0], dict):  # choice is a weighted list
                    choice = r.choices(choice, weights=[e["p"] for e in choice], k=1)[0]
                else:  # choice is a list of strings (evenly weighted)
                    choice = r.choice(choice)
            elif isinstance(choice, dict):
                try:
                    # Will succeed if choice contains a team-based sub-list
                    choice = choice["t"] if self.side == "t" else choice["ct"]
                except KeyError:
                    try:
                        # Will succeed if choice contains a non-team-based sub-list
                        choice = choice["c"]
                    except KeyError:
                        # At this point choice must be a weighted string, with no sub-list
                        choice = choice["n"]
            _purchase_helper(choice)

        for entry in priorities[self.role]:
            _purchase_helper(entry)

    def buy_item(self, choice: str) -> bool:
        buyable = Simulation.items[choice]

        use_price_damaged = False

        if buyable.price > self.money:
            return False

        if buyable.type_ in ("smg", "rifle", "heavy", "pistol"):
            assert isinstance(buyable, _Weapon)
            if buyable.type_ == "pistol":
                self.secondary = buyable
            else:
                self.primary = buyable
        else:
            assert isinstance(buyable, _Equipment)
            if self.limits[buyable.name] == buyable.limit:
                return False
            self.limits[buyable.name] += 1
            if buyable.type_ == "grenade":
                self.grenades.append(buyable)
            elif buyable.name == "kit":
                self.kit = True
            elif buyable.name == "kevlar":
                if self.armor == 100:
                    return False
                self.armor = 100
            elif buyable.name == "helmet":
                if self.helmet:
                    return False
                use_price_damaged = self.armor < 100
                self.armor = 100
                self.helmet = True
        self.money -= buyable.price_damaged if use_price_damaged else buyable.price
        return True

    def __str__(self):
        return (f"Primary: {self.primary.name if self.primary else None}"
                f" | Secondary: {self.secondary.name if self.secondary else None}"
                f" | Grenades: {[g.name for g in self.grenades]} | Money: {self.money}"
                f" | Health: {self.health} | Armor: {self.armor} | Helmet: {self.helmet}"
                f" | Kit: {self.kit} | Side: {self.side} | Role: {self.role}")


class Simulation:
    # These should not be re-assigned inside a Simulation or they will become
    # out of date to other classes, like _Player
    _config: Dict = {}
    items: Dict[str, _Buyable] = {}  # Buyable name mapped to class instance

    def __init__(self, config_path: Path = "config"):
        if isinstance(config_path, str):
            self._config_path = Path(config_path)
        else:
            self._config_path = config_path
        with open(self._config_path / Path("config.yaml")) as config_file:
            self._config.update(yaml.safe_load(config_file))

        if self._config["random_seed"] != 0:
            r.seed(self._config["random_seed"])

        self.t: List[_Player] = []
        self.ct: List[_Player] = []
        self.round_num = 0

        for type_, weapons in self._config["weapons"].items():
            self.items.update({name: _Weapon(data, type_, name) for name, data in weapons.items()})

        for type_, equipment in self._config["equipment"].items():
            self.items.update({name: _Equipment(data, type_, name) for name, data in equipment.items()})

    def start(self):
        self._reset_gamestate()

        # Assign roles
        for p in r.sample(self.t, self._config["player"]["roles"]["awp"]):
            p.role = "awp"
        for p in r.sample(self.ct, self._config["player"]["roles"]["awp"]):
            p.role = "awp"

        self._sim_round()
        # for round_num in range(self._config["rounds"]):
        #     self._sim_round()
        #     self.round_num = round_num

    def _sim_round(self):
        self._buy_period()
        self._assign_positions()
        # self._early_round()
        # self._mid_round()
        # self._late_round()

    def _buy_period(self):
        # Pistol round
        if self.round_num in (0, self._config["rounds"] / 2):
            for player in self._players():
                player.money = self._config["economy"]["starting_money"]
                player.secondary = player.default_secondary

                # Buy mandatory kits before anything else
                for p in r.sample(self.ct, self._config["buy_settings"]["pistol_round"]["kits"]):
                    p.buy_item("kit")
                player.process_purchases(self._config["buy_settings"]["pistol_round"]["purchase_priorities"])

        for player in self._players():
            print(player)

    def _assign_positions(self):
        # Pistol round
        if self.round_num in (0, self._config["rounds"] / 2):
            site_chance = self._config["positioning"]["ct"]["pistol_round"]["a"]["site_chance"].copy()
            for player in r.sample(self.ct, k=len(self.ct)):
                player.position = "a" if site_chance.pop >= r.random() else "b"

    def _reset_gamestate(self):
        self.round_num = 0
        self.t = [_Player({"side": "t"}, self._config["player"]["pistol"]["t"]) for _ in range(5)]
        self.ct = [_Player({"side": "ct"}, self._config["player"]["pistol"]["ct"]) for _ in range(5)]

    def _players(self) -> Generator[_Player, None, None]:
        for player in self.t:
            yield player
        for player in self.ct:
            yield player
