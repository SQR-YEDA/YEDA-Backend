import os
import uuid

import pytest

from app.domain import models
from app.infra.repositories import setup_unit_of_work


@pytest.fixture
def repository():
    fn = "test.db"
    uow = setup_unit_of_work(fn)
    with uow as repository:
        yield repository
    os.remove(fn)


@pytest.fixture
def user_id(repository):
    user_id = uuid.uuid4()
    repository.add_user(
        models.User(
            id=user_id,
            login="test",
            password_hash="test"
        )
    )
    return user_id


def test_user(repository):
    user_id = uuid.uuid4()

    user = repository.get_user_by_login("test")
    assert user is None
    user = repository.get_user(user_id)
    assert user is None

    repository.add_user(
        models.User(
            id=user_id,
            login="test",
            password_hash="test"
        ),
    )

    user = repository.get_user_by_login("test")
    assert user.id == user_id
    user = repository.get_user(user_id)
    assert user.id == user_id


def test_tier_list(repository, user_id):
    tier_lists = repository.get_user_tier_lists(
        user_id=user_id
    )
    assert len(tier_lists) == 0

    elements = repository.get_elements()
    assert len(elements) == 0

    element = models.Element(
        id=uuid.uuid4(),
        name="New Element",
        calories=100
    )
    repository.add_element(element)

    elements = repository.get_elements()
    assert len(elements) == 1
    assert elements[0].id == element.id

    tier_list = models.TierList(
        id=uuid.uuid4(),
        user_id=user_id,
        name="New Tier List",
        categories=[
            models.TierListCategory(
                name="New Category",
                element_ids=[element.id]
            )
        ]
    )
    repository.create_tier_list(tier_list)

    tier_lists = repository.get_user_tier_lists(
        user_id=user_id
    )
    assert len(tier_lists) == 1
    tier_list = tier_lists[0]
    assert tier_list.user_id == user_id
    assert tier_list.name == "New Tier List"
    assert len(tier_lists[0].categories) == 1
    category = tier_lists[0].categories[0]
    assert category.name == "New Category"
    assert len(category.element_ids) == 1
    assert category.element_ids[0] == element.id
