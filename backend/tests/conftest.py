import os
import uuid

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://csuser:devpassword@localhost:5432/construction_store_test"
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.db.base_class import Base
from app.db.session import get_db
from app import models  # noqa: F401 ensures all models are registered
from app.main import app
from app.models.enums import UserRole
from app.models.organization import Company, Site
from app.models.user import User

TEST_DATABASE_URL = "postgresql+psycopg://csuser:devpassword@localhost:5432/construction_store_test"

engine = create_engine(TEST_DATABASE_URL, future=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


@pytest.fixture(scope="function", autouse=True)
def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def site(db_session):
    company = Company(name=f"Test Co {uuid.uuid4().hex[:8]}")
    db_session.add(company)
    db_session.flush()
    s = Site(company_id=company.id, name="Test Site", location="Nairobi")
    db_session.add(s)
    db_session.commit()
    db_session.refresh(s)
    return s


def _make_user(db_session, site, role, email_prefix):
    user = User(
        email=f"{email_prefix}-{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("Password123!"),
        full_name=f"{role.value} Tester",
        role=role,
        company_id=site.company_id,
        site_id=site.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session, site):
    return _make_user(db_session, site, UserRole.ADMIN, "admin")


@pytest.fixture
def storekeeper_user(db_session, site):
    return _make_user(db_session, site, UserRole.STOREKEEPER, "storekeeper")


@pytest.fixture
def manager_user(db_session, site):
    return _make_user(db_session, site, UserRole.MANAGER, "manager")


def auth_headers(client, email: str, password: str = "Password123!") -> dict:
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
