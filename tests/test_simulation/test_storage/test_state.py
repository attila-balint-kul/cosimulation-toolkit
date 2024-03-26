from dataclasses import dataclass, field

import pytest

from cosimtlk.simulation.state import SimulationState


@dataclass
class SubState:
    i: int = field(default=1)
    f: float = field(default=1.0)
    s: str = field(default="sub")


@dataclass
class State(SimulationState):
    i: int = field(default=1)
    f: float = field(default=1.0)
    s: str = field(default="main")
    ss: SubState = field(default_factory=SubState)


@pytest.fixture(scope="function")
def state():
    return State()


def test_setattr_getattr(state):
    assert state.i == 1
    state.i = 2
    assert state.i == 2


def test_setattr_getattr_subclass(state):
    assert state.ss.i == 1
    state.ss.i = 2
    assert state.ss.i == 2


def test_setitem_getitem(state):
    assert state["i"] == 1
    state["i"] = 2
    assert state["i"] == 2


def test_setitem_getitem_subclass(state):
    assert state["ss.i"] == 1
    state["ss.i"] = 2
    assert state["ss.i"] == 2


def test_set_get_single(state):
    state.set(i=2)
    assert state.i == 2


def test_set_get_multiple(state):
    state.set(i=2, f=2.0)
    assert state.i == 2
    assert state.f == 2


def test_set_get_multiple_subclass(state):
    state.set(**{"ss.i": 2, "ss.f": 2.0})
    assert state.ss.i == 2
    assert state.ss.f == 2


if __name__ == "__main__":
    pytest.main()
