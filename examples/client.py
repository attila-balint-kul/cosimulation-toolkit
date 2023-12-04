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

    outputs = client.step(simulator_id, input_values={"int_setpoint": 2, "real_setpoint": 1.0, "bool_setpoint": False})
    logger.info(outputs)

    outputs = client.step(simulator_id, input_values={"int_setpoint": 2, "real_setpoint": 1.0, "bool_setpoint": False})
    logger.info(outputs)

    outputs = client.step(simulator_id, input_values={"int_setpoint": 2, "real_setpoint": 1.0, "bool_setpoint": False})
    logger.info(outputs)

    logger.info("Changing parameter to -2.0")
    client.change_parameters(
        simulator_id, parameters={"integrator.k": -2.0, "integrator.y_start": 3.0}
    )  # carry over state

    outputs = client.step(simulator_id, input_values={"int_setpoint": 2, "real_setpoint": 1.0, "bool_setpoint": False})
    logger.info(outputs)

    outputs = client.step(simulator_id, input_values={"int_setpoint": 2, "real_setpoint": 1.0, "bool_setpoint": False})
    logger.info(outputs)

    logger.info(client.advance(simulator_id, until=15))

    outputs = client.step(simulator_id, input_values={"int_setpoint": 2, "real_setpoint": 1.0, "bool_setpoint": False})
    logger.info(outputs)

    outputs = client.step(simulator_id, input_values={"int_setpoint": 2, "real_setpoint": 1.0, "bool_setpoint": False})
    logger.info(outputs)

    logger.info(client.delete_simulator(simulator_id))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
