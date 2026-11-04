import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from main import app
from shared.clients.database import get_session

TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine_test)

    with Session(engine_test) as session:
        yield session

    with engine_test.connect() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys = OFF;")

        for table in SQLModel.metadata.tables.values():
            conn.exec_driver_sql(f'DROP TABLE IF EXISTS "{table.name}";')

        conn.exec_driver_sql("PRAGMA foreign_keys = ON;")


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()
