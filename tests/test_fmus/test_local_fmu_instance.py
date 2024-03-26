import pytest


def test_initialize(local_fmu_instance):
    assert local_fmu_instance.step_size == 1
    assert local_fmu_instance.current_time == 0


def test_step_on_closed_raises(local_fmu_instance):
    local_fmu_instance.close()
    with pytest.raises(RuntimeError):
        """Cannot call step() on a uninitialized fmu."""
        local_fmu_instance.step()


def test_advance_on_closed_raises(local_fmu_instance):
    local_fmu_instance.close()
    with pytest.raises(RuntimeError):
        """Cannot call advance() on a uninitialized fmu."""
        local_fmu_instance.advance(3)


def test_reset(local_fmu_instance):
    local_fmu_instance.reset(start_time=2, step_size=2, start_values={})

    assert local_fmu_instance.step_size == 2
    assert local_fmu_instance.current_time == 2


def test_reset_multiple_times(local_fmu_instance):
    local_fmu_instance.reset(start_time=1, step_size=1, start_values={})

    local_fmu_instance.reset(start_time=2, step_size=2, start_values={})

    assert local_fmu_instance.step_size == 2
    assert local_fmu_instance.current_time == 2


def test_context_manager(local_fmu_instance):
    with local_fmu_instance as fmu:
        assert fmu.is_initialized is True
        assert fmu.step_size == 1
        assert fmu.current_time == 0

    assert local_fmu_instance.is_initialized is False
    assert local_fmu_instance.step_size == 1
    assert local_fmu_instance.current_time == 0


def test_step(local_fmu):
    k = 2.0
    dt = 1.0
    y = 1.0

    with local_fmu.instantiate(
        start_time=0,
        step_size=1,
        start_values={
            "integrator.k": k,
            "integrator.y_start": y,
        },
    ) as fmu:
        # First step
        outputs = fmu.step(
            input_values={
                "real_setpoint": 2.0,
                "int_setpoint": 3,
                "bool_setpoint": False,
            }
        )
        expected_output = {
            "current_time": 1,
            "real_output": y + k * dt * 2.0,
            "int_output": 3,
            "bool_output": False,
        }
        assert outputs == expected_output

        # Second step
        outputs = fmu.step(
            input_values={
                "real_setpoint": 1.5,
                "int_setpoint": 2,
                "bool_setpoint": False,
            }
        )
        expected_output = {
            "current_time": 2,
            "real_output": y + k * dt * 2.0 + k * dt * 1.5,
            "int_output": 2,
            "bool_output": False,
        }
        assert outputs == expected_output

        # Third step
        outputs = fmu.step(
            input_values={
                "real_setpoint": 3.0,
                "int_setpoint": 2,
                "bool_setpoint": True,  # Resets the integrator
            }
        )
        expected_output = {
            "current_time": 3,
            "real_output": y + k * dt * 3.0,
            "int_output": 2,
            "bool_output": True,
        }
        assert outputs == expected_output


def test_advance(local_fmu):
    with local_fmu.instantiate(
        start_time=0,
        step_size=1,
        start_values={
            "integrator.k": 1.0,
            "integrator.y_start": 1.05,
        },
    ) as fmu:
        outputs = fmu.advance(
            10,
            input_values={
                "real_setpoint": 1.0,
                "int_setpoint": 3,
                "bool_setpoint": True,
            },
        )
        expected_output = {
            "current_time": 10,
            "real_output": 11.05,
            "int_output": 3,
            "bool_output": True,
        }
        assert outputs == expected_output


def test_read_outputs(local_fmu):
    with local_fmu.instantiate(
        start_time=0,
        step_size=1,
        start_values={
            "integrator.k": 2.0,
            "integrator.y_start": 1.05,
            "real_setpoint": 2.0,
            "int_setpoint": 3,
            "bool_setpoint": True,
        },
    ) as fmu:
        outputs = fmu.read_outputs()
        expected_output = {
            "current_time": 0,
            "real_output": 1.05,
            "int_output": 3,
            "bool_output": True,
        }
        assert outputs == expected_output


def test_step_with_custom_stepsize(local_fmu):
    with local_fmu.instantiate(
        start_values={
            "integrator.k": 2.0,
            "integrator.y_start": 1.05,
        },
        step_size=5,
        start_time=1,
    ) as fmu:
        # First step
        outputs = fmu.step(
            input_values={
                "real_setpoint": 1.0,
                "int_setpoint": 3,
                "bool_setpoint": True,
            }
        )
        expected_output = {
            "current_time": 6,
            "real_output": 11.05,
            "int_output": 3,
            "bool_output": True,
        }
        assert outputs == expected_output


def test_advance_with_custom_stepsize(local_fmu):
    with local_fmu.instantiate(
        start_values={
            "integrator.k": 2.0,
            "integrator.y_start": 1.05,
        },
        step_size=5,
        start_time=0,
    ) as fmu:
        # First step
        outputs = fmu.advance(
            11,
            input_values={
                "real_setpoint": 1.0,
                "int_setpoint": 3,
                "bool_setpoint": True,
            },
        )
        expected_output = {
            "current_time": 15,
            "real_output": 31.05,
            "int_output": 3,
            "bool_output": True,
        }
        assert outputs == expected_output


def test_change_parameters(local_fmu):
    with local_fmu.instantiate(
        start_values={
            "integrator.k": 2.0,
            "integrator.y_start": 1.05,
        },
        start_time=0,
        step_size=1,
    ) as fmu:
        outputs = fmu.step(
            input_values={
                "real_setpoint": 1.0,
                "int_setpoint": 3,
                "bool_setpoint": True,
            }
        )
        expected_output = {
            "current_time": 1,
            "real_output": 3.05,
            "int_output": 3,
            "bool_output": True,
        }
        assert outputs == expected_output

        fmu.change_parameters(
            {
                "integrator.k": 1.0,
                # FIXME: this is not ideal that we have to manually carry over state from the previous simulation
                "integrator.y_start": outputs["real_output"],
            }
        )

        outputs = fmu.read_outputs()
        expected_output = {
            "current_time": 1,
            "real_output": 3.05,
            "int_output": 3,
            "bool_output": True,
        }
        assert outputs == expected_output

        outputs = fmu.step(
            input_values={
                "real_setpoint": 1.0,
                "int_setpoint": 2,
                "bool_setpoint": False,
            }
        )
        expected_output = {
            "current_time": 2,
            "real_output": 4.05,
            "int_output": 2,
            "bool_output": False,
        }
        assert outputs == expected_output


if __name__ == "__main__":
    pytest.main()
