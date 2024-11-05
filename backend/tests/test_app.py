from flask import url_for


def test_app(app):
    """Test to make sure the app is loading properly."""

    assert app


def test_index(client):
    """Test that the index works."""

    assert client.get(url_for("api.summary")).status_code == 200
    assert set(client.get(url_for("api.summary")).json.keys()) == {'educational_levels', 'resource_types', 'topics'}