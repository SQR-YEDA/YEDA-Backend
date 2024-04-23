import os

import pytest

from app.domain import usecases
from app.infra.repositories import setup_unit_of_work
from app.presentation.fastapi.app import UpdateTierList, UpdateTierListCategory


@pytest.fixture
def use_case():
    fn = "test.db"
    uow = setup_unit_of_work(fn)
    with uow as repository:
        yield usecases.UseCase(repository)
    os.remove(fn)


@pytest.fixture
def user_id(use_case):
    res = use_case.register_user(
        usecases.RegisterUserRequest(login="test", password="test")
    )
    return use_case.authenticate_via_access_token(
        access_token=res.tokens.access_token
    )


def test_user(use_case):
    access_token = use_case.register_user(
        usecases.RegisterUserRequest(login="test", password="test")
    ).tokens.access_token

    user_id = use_case.authenticate_via_access_token(access_token)
    assert user_id is not None

    access_token = use_case.login_user(
        usecases.LoginUserRequest(login="test", password="test")
    ).tokens.access_token

    user_id_new = use_case.authenticate_via_access_token(access_token)
    assert user_id_new == user_id


def test_get_user_tier_list(use_case, user_id):
    response = use_case.get_user_tier_list(
        usecases.GetUserTierListRequest(user_id=user_id)
    )

    assert response.tier_list.user_id == user_id


def test_elements_and_update_tier_list(use_case, user_id):
    use_case.create_element(
        usecases.CreateElementRequest(
            name="New Element",
            calories=100
        )
    )
    use_case.create_element(
        usecases.CreateElementRequest(
            name="Another Element",
            calories=200
        )
    )

    elements = use_case.get_elements().elements
    assert len(elements) == 2

    update_tier_list = UpdateTierList(
        name="",
        categories=[
            UpdateTierListCategory(
                name="New Category",
                element_ids=[elements[0].id, elements[1].id]
            )
        ]
    )
    use_case.update_user_tier_list(
        usecases.UpdateTierListRequest(
            user_id=user_id, update_tier_list=update_tier_list
        )
    )

    tier_list = use_case.get_user_tier_list(
        usecases.GetUserTierListRequest(user_id=user_id)
    ).tier_list

    assert len(tier_list.categories) == 1
    assert tier_list.categories[0].name == "New Category"
    assert len(tier_list.categories[0].elements) == 2
