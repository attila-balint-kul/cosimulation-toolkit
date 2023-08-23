import pytest

from cosimtlk.simulation.storage import StateStore


@pytest.fixture(scope="function")
def state_store():
    return StateStore()


def test_make_namespace(state_store):
    assert state_store.make_namespace("a") == "a"
    assert state_store.make_namespace("a", "b") == "a:b"
    assert state_store.make_namespace("a", "b", "c") == "a:b:c"


def test_setitem_getitem(state_store):
    state_store["a"] = 1
    assert state_store["a"] == 1
    state_store["a"] = 2
    assert state_store["a"] == 2


def test_setitem_getitem_with_namespace(state_store):
    state_store["a:b"] = 1
    assert state_store["a:b"] == 1
    assert state_store["a"] == {"b": 1}

    state_store["a:b"] = 2
    assert state_store["a:b"] == 2
    assert state_store["a"] == {"b": 2}


def test_get_all(state_store):
    state_store["a"] = 1
    state_store["b"] = 2
    assert state_store.get_all() == {"a": 1, "b": 2}


def test_get_all_with_namespace(state_store):
    state_store["a:b"] = 1
    state_store["a:c"] = 2
    assert state_store.get_all(namespace="a") == {"b": 1, "c": 2}


def test_set_get_single(state_store):
    state_store.set(a=1)
    assert state_store.get("a") == 1
    state_store.set(a=2)
    assert state_store.get("a") == 2


def test_set_get_multiple(state_store):
    state_store.set(a=1, b=2)
    assert state_store.get("a") == 1
    assert state_store.get("b") == 2
    state_store.set(a=2, b=3)
    assert state_store.get("a") == 2
    assert state_store.get("b") == 3


def test_set_get_single_with_namespace(state_store):
    state_store.set(namespace="a", b=1)
    assert state_store.get("a:b") == 1
    assert state_store.get("b", namespace="a") == 1


if __name__ == "__main__":
    pytest.main()
