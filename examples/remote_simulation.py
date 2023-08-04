from cosimtlk.app.client import RemoteFMUSimulator, SimulatorClient


def main():
    client = SimulatorClient.from_parts(port=3000)
    with RemoteFMUSimulator.new(client, "") as simulator:
        print(simulator.info())
        print(simulator.inputs())
        print(simulator.outputs())
        print(simulator.parameters())
        print(simulator.step(input_int=2, input_float=3.16, input_bool=True))
        print(simulator.step(input_int=3, input_float=2.16, input_bool=False))
        print(simulator.step(input_int=4, input_float=1.16, input_bool=True))
        simulator.change_parameters(**{"gain.k": -2.0})
        print(simulator.parameters())
        print(simulator.step(n=2, input_int=5, input_float=2.16, input_bool=False))
        print(simulator.step(n=2, input_int=6, input_float=3.16, input_bool=True))
        print(simulator.step(n=2, input_int=7, input_float=4.16, input_bool=False))
        print(simulator.advance(until=15))


if __name__ == "__main__":
    main()
