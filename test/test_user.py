from unittest.mock import patch


def test_hello(client):
    response = client.get("/users/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello_world"}


def test_create_user(client):
    response = client.post(
        "/users/create-users",
        json={"name": "Sourabh"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Sourabh"
    assert "id" in data


def test_get_all_users(client):
    client.post("/users/create-users", json={"name": "Sourabh"})

    response = client.get("/users/get-all-users")
    assert response.status_code == 200

    users = response.json()
    assert isinstance(users, list)
    assert len(users) >= 1


def test_update_user(client):
    create = client.post(
        "/users/create-users",
        json={"name": "Sourabh"}
    )
    user_id = create.json()["id"]

    response = client.put(
        f"/users/users/{user_id}",
        json={"name": "Aayush"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Aayush"


def test_update_user_not_found(client):
    response = client.put(
        "/users/users/007",
        json={"name": "Sourabh"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_delete_user(client):
    create = client.post(
        "/users/create-users",
        json={"name": "Sourabh"}
    )
    user_id = create.json()["id"]

    response = client.delete(f"/users/users/{user_id}")

    assert response.status_code == 200
    assert response.json() == {"deleted": user_id}


def test_delete_user_not_found(client):
    response = client.delete("/users/users/007")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_simple_upload_file(client):
    response = client.post(
        "/users/uploadfile/",
        files={"file": ("test.txt", b"hello world")}
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "test.txt"


def test_upload_user_file(client):
    create = client.post(
        "/users/create-users",
        json={"name": "Sourabh"}
    )
    user_id = create.json()["id"]

    response = client.post(
        f"/users/upload/{user_id}",
        files={"file": ("image.png", b"something")}
    )

    assert response.status_code == 500


@patch("users.r.get")
def test_find_file_from_cache(mock_redis_get, client):
    mock_redis_get.return_value = b"./uploads/cached.png"

    response = client.get("/users/find-file/1")

    assert response.status_code == 200
    data = response.json()
    assert data["file_path"] == f"./uploads/cached.png"



@patch("users.r.get")
def test_find_file_not_found(mock_redis_get, client):
    mock_redis_get.return_value = None

    response = client.get("/users/find-file/007")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
