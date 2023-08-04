import pytest


def test_init(simulator):
    print(simulator)


def test_closed_raises(simulator):
    simulator.close()
    with pytest.raises(RuntimeError):
        simulator.step()


def test_read_outputs(simulator):
    simulator.reset(init_values={
        'gain.k': 4.0,
        'input_float': 3.14,
        'input_int': 42,
        'input_bool': True,
    })
    outputs = simulator.step(advance_time=False)

    assert outputs == {
        'current_time': 0,
        'outputs': {
            'output_float': 12.56,
            'output_int': 42,
            'output_bool': True,
        }
    }


def test_interested_outputs(simulator):
    simulator.reset(
        output_names=['output_float'],
        init_values={
            'gain.k': 4.0,
            'input_float': 3.14,
            'input_int': 42,
            'input_bool': True,
        }
    )
    outputs = simulator.step(advance_time=False)

    assert outputs == {
        'current_time': 0,
        'outputs': {
            'output_float': 12.56,
        }
    }


def test_step(simulator):
    simulator.reset(init_values={
        'gain.k': 2.0,
    })

    outputs = simulator.step(input_values={
        'input_float': 3.14,
        'input_int': 21,
        'input_bool': False,
    })

    assert outputs == {
        'current_time': 1,
        'outputs': {
            'output_float': 6.28,
            'output_int': 21,
            'output_bool': False,
        }
    }


def test_stepsize(simulator):
    simulator.reset(step_size=5, init_values={
        'gain.k': 2.0,
    })

    outputs = simulator.step(input_values={
        'input_float': 3.14,
        'input_int': 21,
        'input_bool': False,
    })

    assert outputs == {
        'current_time': 5,
        'outputs': {
            'output_float': 6.28,
            'output_int': 21,
            'output_bool': False,
        }
    }


def test_advance(simulator):
    simulator.reset(init_values={
        'gain.k': 2.0,
    })

    outputs = simulator.advance_until(5, input_values={
        'input_float': 3.14,
        'input_int': 21,
        'input_bool': False,
    })

    assert outputs == {
        'current_time': 5,
        'outputs': {
            'output_float': 6.28,
            'output_int': 21,
            'output_bool': False,
        }
    }
