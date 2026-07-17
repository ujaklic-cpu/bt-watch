import pytest

from map_server import HOST_COORDS, app, devices


@pytest.fixture(autouse=True)
def reset_state():
    HOST_COORDS.clear()
    devices.clear()
    yield
    HOST_COORDS.clear()
    devices.clear()


def test_ingest_rejects_invalid_identifiers_and_rssi():
    client = app.test_client()

    assert (
        client.post(
            "/ingest", json={"host": [], "address": "device", "rssi": -50}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/ingest", json={"host": "probe", "address": {}, "rssi": -50}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/ingest", json={"host": "probe", "address": "device", "rssi": "loud"}
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/ingest",
            json={"host": "probe", "address": "device", "rssi": -50, "ts": "never"},
        ).status_code
        == 400
    )


def test_host_coordinates_reject_non_finite_values():
    client = app.test_client()

    response = client.post("/host_coord", json={"host": "probe", "x": "NaN", "y": 1})

    assert response.status_code == 400
    assert "probe" not in HOST_COORDS

    response = client.post("/host_coord", json={"host": [], "x": 0, "y": 1})
    assert response.status_code == 400


def test_sidebar_does_not_render_event_fields_as_html():
    html = app.test_client().get("/").get_data(as_text=True)

    assert "replaceChildren" in html
    assert "textContent = text" in html
    assert "hostList.innerHTML" not in html
