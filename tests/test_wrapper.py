import pytest


def test_init_wrapper(wrapper):
    info = wrapper.info()
    assert info['state']['initialized'] is False
    assert info['state']['current_time'] == 0
    assert info['state']['step_size'] == 1


def test_initialize(wrapper):
    wrapper.initialize()

    info = wrapper.info()
    assert info['state']['initialized'] is True
    assert info['state']['current_time'] == 0
    assert info['state']['step_size'] == 1

    wrapper.close()

    info = wrapper.info()
    assert info['state']['initialized'] is False
    assert info['state']['current_time'] == 0
    assert info['state']['step_size'] == 1


def test_step_on_closed_raises(wrapper):
    with pytest.raises(RuntimeError):
        """Cannot call step() on a uninitialized fmu."""
        wrapper.step()


def test_advance_on_closed_raises(wrapper):
    with pytest.raises(RuntimeError):
        """Cannot call advance() on a uninitialized fmu."""
        wrapper.advance(3)


def test_reset_on_closed_raises(wrapper):
    with pytest.raises(RuntimeError):
        """Cannot call advance() on a uninitialized fmu."""
        wrapper.reset()


def test_context_manager(wrapper):
    with wrapper() as fmu:
        info = fmu.info()
        assert info['state']['initialized'] is True
        assert info['state']['current_time'] == 0
        assert info['state']['step_size'] == 1

    info = wrapper.info()
    assert info['state']['initialized'] is False
    assert info['state']['current_time'] == 0
    assert info['state']['step_size'] == 1


def test_step(wrapper):
    with wrapper(start_values={
        "integrator.k": 2.0,
        "integrator.y_start": 1.05,
    }) as fmu:
        # First step
        outputs = fmu.step(input_values={
            "real_setpoint": 2.0,
            "int_setpoint": 3,
            "bool_setpoint": False,
        })
        expected_output = {'current_time': 1, 'real_output': 5.05, 'int_output': 3, 'bool_output': False}
        assert outputs == expected_output

        # Second step
        outputs = fmu.step(input_values={
            "real_setpoint": 1.0,
            "int_setpoint": 2,
            "bool_setpoint": True,
        })
        expected_output = {'current_time': 2, 'real_output': 7.05, 'int_output': 2, 'bool_output': True}
        assert outputs == expected_output


def test_n_step(wrapper):
    with wrapper(start_values={
        "integrator.k": 2.0,
        "integrator.y_start": 1.05,
    }) as fmu:
        outputs = fmu.step(2, input_values={
            "real_setpoint": 1.0,
            "int_setpoint": 3,
            "bool_setpoint": True,
        })
        expected_output = {'current_time': 2, 'real_output': 5.05, 'int_output': 3, 'bool_output': True}
        assert outputs == expected_output


def test_advance(wrapper):
    with wrapper(start_values={
        "integrator.k": 1.0,
        "integrator.y_start": 1.05,
    }) as fmu:
        outputs = fmu.advance(10, input_values={
            "real_setpoint": 1.0,
            "int_setpoint": 3,
            "bool_setpoint": True,
        })
        expected_output = {'current_time': 10, 'real_output': 11.05, 'int_output': 3, 'bool_output': True}
        assert outputs == expected_output


def test_read_outputs(wrapper):
    with wrapper(start_values={
        "integrator.k": 2.0,
        "integrator.y_start": 1.05,
        "real_setpoint": 2.0,
        "int_setpoint": 3,
        "bool_setpoint": True,
    }) as fmu:
        outputs = fmu.read_outputs()
        expected_output = {'current_time': 0, 'real_output': 1.05, 'int_output': 3, 'bool_output': True}
        assert outputs == expected_output


def test_step_with_custom_stepsize(wrapper):
    with wrapper(start_values={
        "integrator.k": 2.0,
        "integrator.y_start": 1.05,
    }, step_size=5, start_time=1) as fmu:
        # First step
        outputs = fmu.step(input_values={
            "real_setpoint": 1.0,
            "int_setpoint": 3,
            "bool_setpoint": True,
        })
        expected_output = {'current_time': 6, 'real_output': 11.05, 'int_output': 3, 'bool_output': True}
        assert outputs == expected_output


def test_advance_with_custom_stepsize(wrapper):
    with wrapper(start_values={
        "integrator.k": 2.0,
        "integrator.y_start": 1.05,
    }, step_size=5) as fmu:
        # First step
        outputs = fmu.advance(11, input_values={
            "real_setpoint": 1.0,
            "int_setpoint": 3,
            "bool_setpoint": True,
        })
        expected_output = {'current_time': 15, 'real_output': 31.05, 'int_output': 3, 'bool_output': True}
        assert outputs == expected_output


def test_change_parameters(wrapper):
    with wrapper(start_values={
        "integrator.k": 2.0,
        "integrator.y_start": 1.05,
    }) as fmu:
        outputs = fmu.step(input_values={
            "real_setpoint": 1.0,
            "int_setpoint": 3,
            "bool_setpoint": True,
        })
        expected_output = {'current_time': 1, 'real_output': 3.05, 'int_output': 3, 'bool_output': True}
        assert outputs == expected_output

        fmu.change_parameters({
            "integrator.k": 1.0,
            # FIXME: this is not ideal that we have to manually carry over state from the previous simulation
            "integrator.y_start": outputs['real_output'],
        })

        outputs = fmu.read_outputs()
        expected_output = {'current_time': 1, 'real_output': 3.05, 'int_output': 3, 'bool_output': True}
        assert outputs == expected_output
        print(outputs)

        outputs = fmu.step(input_values={
            "real_setpoint": 1.0,
            "int_setpoint": 2,
            "bool_setpoint": False,
        })
        expected_output = {'current_time': 2, 'real_output': 4.05, 'int_output': 2, 'bool_output': False}
        assert outputs == expected_output
        print(outputs)


if __name__ == '__main__':
    pytest.main()
