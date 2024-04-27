import typing
import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.domain import usecases
from app.domain.usecases import UseCase
from app.infra.repositories import uow, Repository

bearer_security = HTTPBearer(auto_error=False)


def get_repository() -> typing.Generator[Repository, None, None]:
    with uow as repository:
        yield repository


def get_use_case(
        repository: Annotated[Repository, Depends(get_repository)]
) -> UseCase:
    return UseCase(repository)


def get_current_user(
        credentials: Annotated[
            HTTPAuthorizationCredentials, Depends(bearer_security)
        ],
        use_case: Annotated[usecases.UseCase, Depends(get_use_case)]
) -> uuid.UUID | None:
    if credentials is None:
        return None
    user_id = use_case.authenticate_via_access_token(credentials.credentials)
    return user_id
