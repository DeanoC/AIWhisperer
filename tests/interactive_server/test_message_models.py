import pytest
from pydantic import BaseModel, ValidationError

class EchoParams(BaseModel):
    message: str

class AddParams(BaseModel):
    a: int
    b: int

def test_echo_params_valid():
    params = EchoParams(message="hello")
    assert params.message == "hello"

def test_echo_params_invalid():
    with pytest.raises(ValidationError):
        EchoParams()

def test_add_params_valid():
    params = AddParams(a=1, b=2)
    assert params.a == 1 and params.b == 2

def test_add_params_invalid():
    with pytest.raises(ValidationError):
        AddParams(a=1)
