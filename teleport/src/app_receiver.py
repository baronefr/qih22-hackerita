from netqasm.sdk import EPRSocket
from netqasm.sdk.external import NetQASMConnection, Socket, get_qubit_state
from netqasm.sdk.toolbox.sim_states import get_fidelity, qubit_from, to_dm
from netqasm.logging.output import get_new_app_logger


def main(app_config=None):
    log_config = app_config.log_config
    app_logger = get_new_app_logger(app_name="receiver", log_config=log_config)
    app_logger.log("receiver main() called")

    # Create a socket to recv classical information
    socket = Socket("receiver", "sender", log_config=log_config)

    # Create a EPR socket for entanglement generation
    epr_socket = EPRSocket("sender")

    # Initialize the connection
    receiver = NetQASMConnection(
        app_name=app_config.app_name, log_config=log_config, epr_sockets=[epr_socket]
    )
    with receiver:
        epr = epr_socket.recv()[0]
        receiver.flush()

        # Get the corrections
        m1, m2 = socket.recv_structured().payload
        print(f"`receiver` got corrections: {m1}, {m2}")
        if m2 == 1:
            print("`receiver` will perform X correction")
            epr.X()
        if m1 == 1:
            print("`receiver` will perform Z correction")
            epr.Z()

        receiver.flush()
        outcome = epr.measure()
        receiver.flush()

    app_logger.log(f"outcome = {outcome}")

    return {
        "correction1": "Z" if m1 == 1 else "None",
        "correction2": "X" if m2 == 1 else "None",
        "measurement_outcome": int(outcome),
    }


if __name__ == "__main__":
    main()

