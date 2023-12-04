import pytest
from fmpy.model_description import ModelDescription

from cosimtlk import FMU, FMUInstance


def test_can_instantiate():
    FMU("tests/fixtures/fmus/ModSim.Examples.InputTest.fmu")


def test_model_description(local_fmu):
    assert isinstance(local_fmu.model_description, ModelDescription)


def test_inputs(local_fmu):
    for input_ in local_fmu.inputs:
        assert input_.causality == "input"


def test_outputs(local_fmu):
    for output in local_fmu.outputs:
        assert output.causality == "output"


def test_parameters(local_fmu):
    for parameter in local_fmu.parameters:
        assert parameter.causality == "parameter"


def test_instantiate(local_fmu):
    fmu = local_fmu.instantiate(
        start_time=0,
        step_size=1,
        start_values={},
    )
    assert isinstance(fmu, FMUInstance)


if __name__ == "__main__":
    pytest.main()
