import pytest

from cosimtlk.simulators import FMUSimulator


@pytest.fixture(scope="function")
def simulator():
    path = "/examples/fmus/RealBoolIntTest.fmu"
    simulator = FMUSimulator(path)
    yield simulator
    simulator.close()
