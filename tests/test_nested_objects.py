"""Integration tests for automatically mapped nested objects."""

# pylint: disable=redefined-outer-name,expression-not-assigned

import pytest
from expecter import expect

import yorm


@yorm.attr(arg=yorm.types.Integer)
@yorm.attr(kwarg=yorm.types.Integer)
@yorm.sync("tmp/inner.yml")
class Inner:

    def __init__(self, arg, kwarg=42):
        self.arg = arg
        self.kwarg = kwarg


@yorm.attr(inner=Inner)
@yorm.sync("tmp/{self.filename}")
class Outer:

    def __init__(self, filename="outer.yml", inner=None):
        self.filename = filename
        self.inner = inner


@pytest.fixture
def outer():
    return Outer()


def test_inner_object_initializes(outer):
    expect(outer.inner.arg) == 0
    expect(outer.inner.kwarg) == 0
