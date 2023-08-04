from cosimtlk.app.client import SimulatorClient


def main():
    client = SimulatorClient.from_parts(port=3000)

    print(client.reset(step_size=1, output_names=None, init_values={"gain.k": 1}))
    print(client.info())
    print(client.parameters())
    print(client.step(input_values=dict(input_int=1, input_float=3.14, input_bool=True)))
    print(client.step(input_values=dict(input_int=2, input_float=3.14, input_bool=False)))
    print(client.step(input_values=dict(input_int=3, input_float=3.14, input_bool=True)))

    print(client.reset(step_size=2, output_names=None, init_values={"gain.k": -3}))
    print(client.info())
    print(client.parameters())
    print(client.step(input_values=dict(input_int=1, input_float=1.1, input_bool=True)))
    print(client.step(input_values=dict(input_int=2, input_float=1.1, input_bool=False)))
    print(client.step(input_values=dict(input_int=3, input_float=1.1, input_bool=True)))


if __name__ == "__main__":
    main()
