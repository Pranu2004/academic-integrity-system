from app import app


def test_dashboard_loads():
    app.config["TESTING"] = True
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200


def test_case_detail_loads():
    app.config["TESTING"] = True
    client = app.test_client()

    response = client.get("/case/CASE-0115")

    assert response.status_code == 200
    assert b"CASE-0115" in response.data
