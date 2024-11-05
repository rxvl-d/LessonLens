import pytest
from flask import Flask
from pytest_flask.fixtures import client

from ll import init_webapp

assert client

@pytest.fixture(scope='module')
def app(request):
    app = init_webapp(test=True)
    ctx = app.app_context()
    ctx.push()
    def teardown():
        ctx.pop()
    request.addfinalizer(teardown)
    return app