import uuid
from dataclasses import dataclass


@dataclass
class User:
    id: uuid.UUID
    login: str
    password_hash: str


@dataclass
class Element:
    id: uuid.UUID
    name: str
    calories: int


@dataclass
class TierListCategory:
    name: str
    element_ids: list[uuid.UUID]


@dataclass
class TierList:
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    categories: list[TierListCategory]
