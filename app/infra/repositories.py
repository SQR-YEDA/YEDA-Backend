import uuid
from typing import List

from sqlalchemy import types, ForeignKey, create_engine, select, delete
from sqlalchemy.orm import (Session, DeclarativeBase, Mapped,
                            mapped_column, relationship, sessionmaker)

from app.domain import models


class Repository:
    def __init__(self, session: Session):
        self.session = session

    def add_user(self, user: models.User):
        repo_user = User(
            id=str(user.id),
            login=user.login,
            password_hash=user.password_hash
        )
        self.session.add(repo_user)

    def get_user(self, user_id: uuid.UUID) -> models.User | None:
        stmt = (select(User)
                .where(User.id == str(user_id)))
        repo_user = self.session.scalar(stmt)
        if repo_user is None:
            return None
        return models.User(
            id=uuid.UUID(repo_user.id),
            login=repo_user.login,
            password_hash=repo_user.password_hash
        )

    def get_user_by_login(self, login: str) -> models.User | None:
        stmt = (select(User)
                .where(User.login == login))
        repo_user = self.session.scalar(stmt)
        if repo_user is None:
            return None
        return models.User(
            id=uuid.UUID(repo_user.id),
            login=repo_user.login,
            password_hash=repo_user.password_hash
        )

    def get_elements(self) -> list[models.Element]:
        stmt = select(Element)
        repo_elements = self.session.scalars(stmt).all()
        return [models.Element(
            id=uuid.UUID(repo_element.id),
            name=repo_element.name,
            calories=repo_element.calories
        ) for repo_element in repo_elements]

    def add_element(self, element: models.Element):
        repo_element = Element(
            id=str(element.id),
            name=element.name,
            calories=element.calories
        )
        self.session.add(repo_element)

    def get_element(self, element_id: uuid.UUID) -> models.Element:
        stmt = (select(Element)
                .where(Element.id == str(element_id)))
        repo_element = self.session.scalar(stmt)
        return models.Element(
            id=uuid.UUID(repo_element.id),
            name=repo_element.name,
            calories=repo_element.calories
        )

    def get_user_tier_lists(self, user_id: uuid.UUID) -> list[models.TierList]:
        stmt = (select(TierList)
                .where(TierList.user_id == str(user_id)))
        repo_tier_lists = self.session.scalars(stmt).all()
        return [_repo_to_model_tier_list(repo_tier_list)
                for repo_tier_list in repo_tier_lists]

    def create_tier_list(self, tier_list: models.TierList):
        repo_tier_list = _model_to_repo_tier_list(tier_list)
        self.session.add(repo_tier_list)

    def update_tier_list(
            self, tier_list_id: uuid.UUID, tier_list: models.TierList
    ):
        repo_tier_list = _model_to_repo_tier_list(tier_list)
        repo_tier_list.id = str(tier_list_id)

        select_repo_tl_categories_stmt = (
            select(TierListCategory)
            .where(TierListCategory.tier_list_id == str(tier_list_id)))
        repo_tl_categories = (self.session
                              .scalars(select_repo_tl_categories_stmt).all())

        delete_repo_tl_elements_stmt = (
            delete(TierListElement)
            .where(TierListElement.tier_list_category_id
                   .in_([category.id for category in repo_tl_categories]
                        )))
        self.session.execute(delete_repo_tl_elements_stmt)
        delete_repo_tl_categories_stmt = (
            delete(TierListCategory)
            .where(TierListCategory.tier_list_id == str(tier_list_id)))
        self.session.execute(delete_repo_tl_categories_stmt)

        self.session.merge(repo_tier_list)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[str] = mapped_column(types.String, primary_key=True)
    login: Mapped[str] = mapped_column(types.String, nullable=False)
    password_hash: Mapped[str] = mapped_column(types.String, nullable=False)


class TierList(Base):
    __tablename__ = 'tier_lists'

    id: Mapped[str] = mapped_column(types.String, primary_key=True)
    user_id: Mapped[str] = mapped_column(
        ForeignKey('users.id'), nullable=False
    )
    name: Mapped[str] = mapped_column(types.String, nullable=False)

    categories: Mapped[List['TierListCategory']] = relationship(
        order_by='TierListCategory.number'
    )


class TierListCategory(Base):
    __tablename__ = 'tier_list_categories'

    id: Mapped[str] = mapped_column(types.String, primary_key=True)
    tier_list_id: Mapped[str] = mapped_column(
        ForeignKey('tier_lists.id'), nullable=False
    )
    number: Mapped[int] = mapped_column(types.Integer, nullable=False)
    name: Mapped[str] = mapped_column(types.String, nullable=False)

    elements: Mapped[List['TierListElement']] = relationship(
        order_by='TierListElement.number'
    )


class Element(Base):
    __tablename__ = 'elements'

    id: Mapped[str] = mapped_column(types.String, primary_key=True)
    name: Mapped[str] = mapped_column(types.String, nullable=False)
    calories: Mapped[int] = mapped_column(types.Integer, nullable=False)


class TierListElement(Base):
    __tablename__ = 'tier_list_elements'

    tier_list_category_id: Mapped[str] = mapped_column(
        ForeignKey('tier_list_categories.id'), primary_key=True
    )
    number: Mapped[int] = mapped_column(types.Integer, primary_key=True)
    element_id: Mapped[str] = mapped_column(
        ForeignKey('elements.id'), primary_key=True
    )


def _repo_to_model_tier_list(repo_tier_list: TierList) -> models.TierList:
    return models.TierList(
        id=uuid.UUID(repo_tier_list.id),
        user_id=uuid.UUID(repo_tier_list.user_id),
        name=repo_tier_list.name,
        categories=[
            models.TierListCategory(
                name=repo_category.name,
                element_ids=[
                    repo_element.element_id
                    for repo_element in repo_category.elements
                ]
            )
            for repo_category in repo_tier_list.categories
        ]
    )


def _model_to_repo_tier_list(model_tier_list: models.TierList) -> TierList:
    def get_repo_category(
            category: models.TierListCategory,
            tier_list_id: uuid.UUID, number: int
    ) -> TierListCategory:
        category_id = str(uuid.uuid4())
        return TierListCategory(
            id=category_id,
            tier_list_id=str(tier_list_id),
            name=category.name,
            number=number,
            elements=[
                TierListElement(
                    number=element_num,
                    tier_list_category_id=category_id,
                    element_id=str(element_id)
                )
                for element_num, element_id in enumerate(category.element_ids)
            ]
        )

    return TierList(
        id=str(model_tier_list.id),
        user_id=str(model_tier_list.user_id),
        name=model_tier_list.name,
        categories=[
            get_repo_category(category, model_tier_list.id, category_num)
            for category_num, category in enumerate(model_tier_list.categories)
        ]
    )


class UnitOfWork:
    def __init__(self, session_maker: sessionmaker):
        self.session_maker = session_maker

    def __enter__(self) -> 'Repository':
        self.session = self.session_maker()
        return Repository(self.session)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.session.commit()
        else:
            self.session.rollback()
        self.session.close()


def setup_unit_of_work() -> UnitOfWork:
    url = 'sqlite:///database.db'
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    session_maker = sessionmaker(bind=engine)
    return UnitOfWork(session_maker)


uow = setup_unit_of_work()
