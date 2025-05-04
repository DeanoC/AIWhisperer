from dotenv import load_dotenv
import os
import pytest

load_dotenv()

@pytest.fixture
def api_key():
    return os.getenv("API_KEY")

@pytest.fixture
def client():
    # Setup code for your test client
    pass

@pytest.fixture
def some_other_fixture():
    # Setup code for another fixture
    pass