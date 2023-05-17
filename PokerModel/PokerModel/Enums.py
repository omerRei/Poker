from enum import Enum


class Position(Enum):
    SMALL_BLIND = 0
    BIG_BLIND = 1
    CHECK = 2
    CALL = 3
    RAISE = 4


class Action(Enum):
    FOLD = 0
    CHECK_CALL = 1
    RAISE_BIG_BLIND = 2
    RAISE_HALF_POT = 3
    RAISE_POT = 4
    RAISE_TWO_POT = 5
