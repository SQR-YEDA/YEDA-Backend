import uuid
from typing import Annotated

from fastapi import APIRouter, FastAPI, Depends, HTTPException
from pydantic import BaseModel

from app.domain import usecases
from app.presentation.fastapi.deps import get_use_case, get_current_user

tier_list_router = APIRouter(tags=["TierList"])


class Element(BaseModel):
    """
    Represents an element in a tier list.
    """
    id: uuid.UUID
    name: str
    calories: int


class GetElementsResponse(BaseModel):
    """
    Response model for fetching elements.
    """
    elements: list[Element]


@tier_list_router.get("/elements")
def get_elements(
        current_user: Annotated[uuid.UUID | None, Depends(get_current_user)],
        use_case: Annotated[usecases.UseCase, Depends(get_use_case)]
) -> GetElementsResponse:
    """
    Retrieve elements from the tier list.
    """
    if current_user is None:
        raise HTTPException(status_code=403, detail="Forbidden")
    res = use_case.get_elements()
    return GetElementsResponse(elements=[Element(
        id=element.id,
        name=element.name,
        calories=element.calories
    ) for element in res.elements])


class CreateElementRequest(BaseModel):
    """
    Request model for creating a new element.
    """
    name: str
    calories: int


@tier_list_router.post("/elements")
def create_element(
        request: CreateElementRequest,
        current_user_id: Annotated[
            uuid.UUID | None, Depends(get_current_user)
        ],
        use_case: Annotated[usecases.UseCase, Depends(get_use_case)]
):
    """
    Create a new element.
    """
    if current_user_id is None:
        raise HTTPException(status_code=403, detail="Forbidden")
    use_case.create_element(
        usecases.CreateElementRequest(
            name=request.name,
            calories=request.calories
        )
    )


class GetTierListCategory(BaseModel):
    """
    Represents a category in a tier list.
    """
    name: str
    elements: list[Element]


class GetTierList(BaseModel):
    """
    Represents a tier list.
    """
    name: str
    categories: list[GetTierListCategory]


class GetTierListResponse(BaseModel):
    """
    Response model for fetching tier lists.
    """
    tier_list: GetTierList


@tier_list_router.get("/tier-list")
def get_user_tier_list(
        current_user_id: Annotated[
            uuid.UUID | None, Depends(get_current_user)
        ],
        use_case: Annotated[usecases.UseCase, Depends(get_use_case)]
) -> GetTierListResponse:
    """
    Retrieve the tier list of the current user.
    """
    if current_user_id is None:
        raise HTTPException(status_code=403, detail="Forbidden")
    res = use_case.get_user_tier_list(
        usecases.GetUserTierListRequest(user_id=current_user_id)
    )
    return GetTierListResponse(tier_list=GetTierList(
        name=res.tier_list.name,
        categories=[GetTierListCategory(
            name=category.name,
            elements=[Element(
                id=element.id,
                name=element.name,
                calories=element.calories
            ) for element in category.elements]
        ) for category in res.tier_list.categories]
    ))


class UpdateTierListCategory(BaseModel):
    """
    Request model for updating a category in a tier list.
    """
    name: str
    element_ids: list[uuid.UUID]


class UpdateTierList(BaseModel):
    """
    Request model for updating a tier list.
    """
    name: str
    categories: list[UpdateTierListCategory]


class UpdateTierListRequest(BaseModel):
    """
    Request model for updating a tier list.
    """
    update_tier_list: UpdateTierList


@tier_list_router.put("/tier-list")
def update_user_tier_list(
        request: UpdateTierListRequest,
        current_user_id: Annotated[
            uuid.UUID | None, Depends(get_current_user)
        ],
        use_case: Annotated[usecases.UseCase, Depends(get_use_case)]
):
    """
    Update the tier list of the current user.
    """
    if current_user_id is None:
        raise HTTPException(status_code=403, detail="Forbidden")
    use_case.update_user_tier_list(
        usecases.UpdateTierListRequest(
            user_id=current_user_id,
            update_tier_list=usecases.UpdateTierList(
                name=request.update_tier_list.name,
                categories=[usecases.UpdateTierListCategory(
                    name=category.name,
                    element_ids=category.element_ids
                ) for category in request.update_tier_list.categories]
            )
        )
    )


auth_router = APIRouter(tags=["Auth"])


class Tokens(BaseModel):
    """
    Represents authentication tokens.
    """
    access_token: str


class RegisterUserRequest(BaseModel):
    """
    Request model for registering a new user.
    """
    login: str
    password: str


class RegisterUserResponse(BaseModel):
    """
    Response model for registering a new user.
    """
    tokens: Tokens


@auth_router.post("/register")
def register_user(
        request: RegisterUserRequest,
        use_case: Annotated[usecases.UseCase, Depends(get_use_case)],
) -> RegisterUserResponse:
    """
    Register a new user.
    """
    try:
        res = use_case.register_user(
            usecases.RegisterUserRequest(
                login=request.login, password=request.password
            )
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Login is already taken")
    return RegisterUserResponse(
        tokens=Tokens(access_token=res.tokens.access_token)
    )


class LoginUserRequest(BaseModel):
    """
    Request model for logging in a user.
    """
    login: str
    password: str


class LoginUserResponse(BaseModel):
    """
    Response model for logging in a user.
    """
    tokens: Tokens


@auth_router.post("/login")
def login_user(
        request: LoginUserRequest,
        use_case: Annotated[usecases.UseCase, Depends(get_use_case)]
) -> LoginUserResponse:
    """
    Log in a user.
    """
    try:
        res = use_case.login_user(
            usecases.LoginUserRequest(login=request.login,
                                      password=request.password)
        )
    except ValueError:
        raise HTTPException(
            status_code=401, detail="Incorrect login or password"
        )
    return LoginUserResponse(
        tokens=Tokens(access_token=res.tokens.access_token)
    )


def get_app():
    app = FastAPI()

    app.include_router(auth_router)
    app.include_router(tier_list_router)

    return app
