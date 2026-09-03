import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.security import hash_password
from app.db.base import Base
from app.main import app
from app.models.user import User
from app.seeds import seed_defaults as seed_defaults_module

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://ticketsystem:ticketsystem@localhost:5432/ticketsystem_test",
)


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DATABASE_URL, future=True)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture(scope="session", autouse=True)
def _seeded(engine):
    from sqlalchemy.orm import sessionmaker

    original_session_local = seed_defaults_module.SessionLocal
    seed_defaults_module.SessionLocal = sessionmaker(bind=engine, future=True)
    try:
        seed_defaults_module.run()
    finally:
        seed_defaults_module.SessionLocal = original_session_local


@pytest.fixture()
def db_session(engine):
    """Wraps each test in an outer transaction that's rolled back afterwards. Uses
    join_transaction_mode='create_savepoint' so that app-code calls to session.commit()
    only commit a SAVEPOINT, leaving the outer transaction (and full test isolation) intact."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db_session):
    counter = {"n": 0}

    def _make_user(email: str | None = None, password: str = "password123", display_name: str = "Test User"):
        counter["n"] += 1
        email = email or f"user{counter['n']}@example.com"
        user = User(email=email, display_name=display_name, password_hash=hash_password(password))
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user, password

    return _make_user


@pytest.fixture()
def auth_client(client, make_user):
    """Returns (client, user, headers) for a freshly created, logged-in user."""

    def _auth_client(**kwargs):
        user, password = make_user(**kwargs)
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": user.email, "password": password},
        )
        assert resp.status_code == 200, resp.text
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        return user, headers

    return _auth_client
