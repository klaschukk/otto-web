import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DB_PATH": str(tmp_path / "t.db"),
                       "ADMIN_USER": "admin", "ADMIN_PASSWORD": "secret-pass", "SECRET_KEY": "test"})


@pytest.fixture
def client(app):
    return app.test_client()
