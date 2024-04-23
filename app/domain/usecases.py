import uuid
from dataclasses import dataclass

import jwt

from app.config import config
from app.domain import models
from app.infra.repositories import Repository


@dataclass
class GetUserTierListRequest:
    user_id: uuid.UUID


@dataclass
class GetTierList:
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    categories: list['GetTierListCategory']


@dataclass
class GetTierListCategory:
    name: str
    elements: list['Element']


@dataclass
class Element:
    id: uuid.UUID
    name: str
    calories: int


@dataclass
class CreateElementRequest:
    name: str
    calories: int


@dataclass
class GetUserTierListResponse:
    tier_list: GetTierList


@dataclass
class UpdateTierList:
    name: str
    categories: list['UpdateTierListCategory']


@dataclass
class UpdateTierListCategory:
    name: str
    element_ids: list[uuid.UUID]


@dataclass
class UpdateTierListRequest:
    user_id: uuid.UUID
    update_tier_list: UpdateTierList


@dataclass
class GetElementsResponse:
    elements: list[Element]


@dataclass
class Tokens:
    access_token: str


@dataclass
class RegisterUserRequest:
    login: str
    password: str


@dataclass
class RegisterUserResponse:
    tokens: Tokens


@dataclass
class LoginUserRequest:
    login: str
    password: str


@dataclass
class LoginUserResponse:
    tokens: Tokens


class UseCase:
    def __init__(self, repository: Repository):
        self.repository = repository

    def register_user(self, request: RegisterUserRequest) -> RegisterUserResponse:
        login_user = self.repository.get_user_by_login(request.login)
        if login_user is not None:
            raise ValueError("Login is already taken")
        user = models.User(
            id=uuid.uuid4(),
            login=request.login,
            password_hash=hash_password(request.password)
        )
        self.repository.add_user(user)
        tier_list = models.TierList(
            id=uuid.uuid4(),
            user_id=user.id,
            name="",
            categories=[]
        )
        self.repository.create_tier_list(tier_list)
        return RegisterUserResponse(tokens=Tokens(access_token=create_access_token(user.id)))

    def login_user(self, request: LoginUserRequest) -> LoginUserResponse:
        user = self.repository.get_user_by_login(request.login)
        if user is None:
            raise ValueError("User not found")
        if not compare_passwords(request.password, user.password_hash):
            raise ValueError("Invalid password")
        return LoginUserResponse(tokens=Tokens(access_token=create_access_token(user.id)))

    def authenticate_via_access_token(self, access_token: str) -> uuid.UUID | None:
        user_id = get_user_from_access_token(access_token)
        user = self.repository.get_user(user_id)
        if user is None:
            return None
        return user.id

    def get_elements(self) -> GetElementsResponse:
        elements = self.repository.get_elements()
        return GetElementsResponse(elements=[
            Element(
                id=element.id,
                name=element.name,
                calories=element.calories
            )
            for element in elements
        ])

    def create_element(self, request: CreateElementRequest):
        element = models.Element(
            id=uuid.uuid4(),
            name=request.name,
            calories=request.calories
        )
        self.repository.add_element(element)

    def get_user_tier_list(self, request: GetUserTierListRequest) -> GetUserTierListResponse:
        def get_element(element_id: uuid.UUID) -> Element:
            element = self.repository.get_element(element_id)
            return Element(
                id=element.id,
                name=element.name,
                calories=element.calories
            )

        user_id = request.user_id
        user_tier_lists = self.repository.get_user_tier_lists(user_id)
        tier_list = user_tier_lists[0]
        return GetUserTierListResponse(tier_list=GetTierList(
            id=tier_list.id,
            user_id=tier_list.user_id,
            name=tier_list.name,
            categories=[
                GetTierListCategory(
                    name=category.name,
                    elements=[
                        get_element(element_id)
                        for element_id in category.element_ids
                    ]
                )
                for category in tier_list.categories
            ]
        ))

    def update_user_tier_list(self, request: UpdateTierListRequest):
        user_id = request.user_id
        update_tier_list = request.update_tier_list
        tier_list = self.repository.get_user_tier_lists(user_id)[0]
        self.repository.update_tier_list(tier_list.id, models.TierList(
            id=tier_list.id,
            user_id=tier_list.user_id,
            name=update_tier_list.name,
            categories=[
                models.TierListCategory(
                    name=category.name,
                    element_ids=category.element_ids
                )
                for category in update_tier_list.categories
            ]
        ))


def hash_password(password: str) -> str:
    return password


def compare_passwords(password: str, password_hash: str) -> bool:
    return password == password_hash


def create_access_token(user_id: uuid.UUID) -> str:
    return jwt.encode({"user_id": str(user_id)}, config.jwt_secret_key, algorithm="HS256")


def get_user_from_access_token(access_token: str) -> uuid.UUID | None:
    access_token_bytes = access_token.encode("utf-8")
    try:
        payload = jwt.decode(access_token_bytes, config.jwt_secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    return uuid.UUID(payload["user_id"])
