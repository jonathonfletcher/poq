
import dataclasses


@dataclasses.dataclass(frozen=True)
class System:
    system_id: int
    name: str
    neighbours: frozenset[int]


@dataclasses.dataclass(frozen=True)
class Character:
    character_id: int
    name: str
