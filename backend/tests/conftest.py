from uuid import uuid4
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app

from app.auth.models import Permission, Role
from app.users.models import User

TEST_DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{settings.DATABASE_USER}:"
    f"{settings.DATABASE_PASSWORD}@"
    f"{settings.DATABASE_HOST}:"
    f"{settings.DATABASE_PORT}/"
    f"psicodesk_test"
)

test_engine = create_engine(
    TEST_DATABASE_URL,
    echo=False,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(
        bind=connection,
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(
    db: Session,
) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    
@pytest.fixture
def auth_headers(
    client: TestClient,
) -> dict[str, str]:
    email = "authenticated@example.com"
    password = "password-test-123"

    register_response = client.post(
        "/users",
        json={
            "email": email,
            "password": password,
            "first_name": "Authenticated",
            "last_name": "User",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }
    
@pytest.fixture
def professional_factory(
    client: TestClient,
    db: Session,
):
    def create_professional() -> dict[str, str]:
        unique_id = uuid4().hex

        email = f"professional-{unique_id}@example.com"
        password = "password-test-123"

        register_response = client.post(
            "/users",
            json={
                "email": email,
                "password": password,
                "first_name": "Professional",
                "last_name": "Test",
            },
        )

        assert register_response.status_code == 201

        user = db.scalar(
            select(User).where(User.email == email)
        )

        assert user is not None

        role = Role(
            name=f"professional-test-{unique_id}",
        )
        
        db.add(role)
        db.flush()

        permission_codes = [
            "patients.read",
            "patients.create",
            "patients.update",
            "patients.delete",
        ]

        for code in permission_codes:
            permission = db.scalar(
                select(Permission).where(
                    Permission.code == code
                )
            )

            if permission is None:
                permission = Permission(code=code)
                db.add(permission)
                db.flush()

            role.permissions.append(permission)

        user.roles.append(role)

        db.commit()

        login_response = client.post(
            "/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )

        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        return {
            "Authorization": f"Bearer {token}"
        }

    return create_professional


@pytest.fixture
def professional_headers(
    professional_factory,
) -> dict[str, str]:
    return professional_factory()