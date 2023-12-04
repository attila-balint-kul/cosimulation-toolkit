import logging

from cosimtlk import FMU

logger = logging.getLogger(__name__)


def main():
    fmu = FMU("../fmus/ModSim.Examples.InputTest.fmu")
    logger.info(fmu.model_description)
    logger.info(fmu.inputs)
    logger.info(fmu.outputs)
    logger.info(fmu.parameters)

    with fmu.instantiate(
        start_time=0,
        step_size=1,
        start_values={
            "integrator.k": 1.0,
        },
    ) as fmu_instance:
        logger.info(fmu_instance)
        logger.info(fmu_instance.step(input_values={"int_setpoint": 2, "real_setpoint": 1, "bool_setpoint": False}))
        logger.info(fmu_instance.step(input_values={"int_setpoint": 2, "real_setpoint": 1, "bool_setpoint": False}))
        logger.info(fmu_instance.step(input_values={"int_setpoint": 2, "real_setpoint": 1, "bool_setpoint": False}))
        logger.info("Changing parameter to -2.0")
        fmu_instance.change_parameters(parameters={"integrator.k": -2.0, "integrator.y_start": 3.0})  # carry over state
        logger.info(fmu_instance.step(input_values={"int_setpoint": 2, "real_setpoint": 1, "bool_setpoint": False}))
        logger.info(fmu_instance.step(input_values={"int_setpoint": 2, "real_setpoint": 1, "bool_setpoint": False}))
        logger.info(fmu_instance.advance(until=15))
        logger.info(fmu_instance.step(input_values={"int_setpoint": 2, "real_setpoint": 1, "bool_setpoint": False}))
        logger.info(fmu_instance.step(input_values={"int_setpoint": 2, "real_setpoint": 1, "bool_setpoint": False}))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
