import logging

from cosimtlk.app.client import SimulatorClient

logger = logging.getLogger(__name__)


def main():
    client = SimulatorClient.from_parts(port=8000)
    logger.info(f"Simulators: {client.list_simulators()}")

    # Create new simulator
    simulator = client.create_simulator(
        "ModSim.Examples.InputTest",
        start_time=0,
        step_size=1,
        start_values={
            "integrator.k": 1.0,
        },
    )
    simulator_id = simulator.id
    logger.info(f"Created simulator: {simulator}")
    logger.info(f"Simulators: {client.list_simulators()}")

    logger.info(
        f"Step 1: {client.step(simulator_id, input_values={'int_setpoint': 1, 'real_setpoint': 3.14, 'bool_setpoint': True,})}"
    )
    logger.info(
        f"Step 2: {client.step(simulator_id, input_values={'int_setpoint': 2, 'real_setpoint': 3.14, 'bool_setpoint': False,})}"
    )
    logger.info(
        f"Step 3: {client.step(simulator_id, input_values={'int_setpoint': 3, 'real_setpoint': 3.14, 'bool_setpoint': True,})}"
    )
    logger.info(f"Reset {client.reset(simulator_id, start_values={'integrator.k': -3}, start_time=0, step_size=2)}")
    logger.info(
        f"Step 1: {client.step(simulator_id, input_values={'int_setpoint': 1, 'real_setpoint': 3.14, 'bool_setpoint': True,})}"
    )
    logger.info(f"Outputs: {client.get_outputs(simulator_id)}")
    logger.info(client.delete_simulator(simulator_id))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
