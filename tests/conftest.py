import os

import pytest


def pytest_configure(config):
    os.environ["DEBUG"] = "True"
