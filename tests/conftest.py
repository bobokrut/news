import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def tests_setup_and_teardown():
    # Will be executed before the first test
    old_environ = dict(os.environ)
    os.environ["DEBUG"] = "True"

    yield
    # Will be executed after the last test
    os.environ.clear()
    os.environ.update(old_environ)
