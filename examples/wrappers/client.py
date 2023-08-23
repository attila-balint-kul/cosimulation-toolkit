from cosimtlk.app.client import SimulatorClient


def main():
    client = SimulatorClient.from_parts(port=8000)
    print(f"Simulators: {client.list_simulators()}")

    # Create new simulator
    simulator = client.create_simulator(
        "RealBoolIntTest",
        start_values={
            "gain.k": 1
        },
        start_time=1,
        step_size=2,
    )
    simulator_id = simulator.id
    print(f"Created simulator: {simulator}")
    print(f"Simulators: {client.list_simulators()}")

    print("Step 1: ", client.step(simulator_id, input_values=dict(input_int=1, input_float=3.14, input_bool=True)))
    print("Step 2: ",client.step(simulator_id, input_values=dict(input_int=2, input_float=3.14, input_bool=False)))
    print("Step 3: ",client.step(simulator_id, input_values=dict(input_int=3, input_float=3.14, input_bool=True)))

    print("Reset ", client.reset(simulator_id, start_values={"gain.k": -3}, start_time=0, step_size=2))
    print("Step 1: ", client.step(simulator_id, input_values=dict(input_int=1, input_float=3.14, input_bool=True)))
    print("Outputs: ", client.get_outputs(simulator_id))

    print(client.delete_simulator(simulator_id))


if __name__ == "__main__":
    main()
