import pytest

import app as app_module


@pytest.fixture(autouse=True)
def reset_state():
    """Start every test with an empty task list."""
    app_module.tasks.clear()
    app_module.next_id = 1
    yield


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as client:
        yield client


def test_home_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Task Manager" in response.data


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_add_task(client):
    response = client.post("/add", data={"title": "Learn CI/CD"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Learn CI/CD" in response.data


def test_empty_title_is_ignored(client):
    client.post("/add", data={"title": "   "})
    assert app_module.tasks == []


def test_toggle_task(client):
    client.post("/add", data={"title": "Write tests"})
    client.post("/toggle/1")
    assert app_module.tasks[0]["done"] is True
    client.post("/toggle/1")
    assert app_module.tasks[0]["done"] is False


def test_delete_task(client):
    client.post("/add", data={"title": "Temporary task"})
    client.post("/delete/1")
    assert app_module.tasks == []


def test_unknown_route_returns_404(client):
    assert client.get("/does-not-exist").status_code == 404
