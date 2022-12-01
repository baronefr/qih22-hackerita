from netqasm.sdk import EPRSocket
from netqasm.sdk.external import NetQASMConnection, Socket, get_qubit_state
from netqasm.sdk.toolbox.sim_states import get_fidelity, qubit_from, to_dm
from netqasm.logging.output import get_new_app_logger


def main(app_config=None):
    log_config = app_config.log_config
    app_logger = get_new_app_logger(app_name="receiver2", log_config=log_config)
    app_logger.log("receiver2 main() called")

    # Create a socket to recv classical information
    socket = Socket("receiver2", "sender", log_config=log_config)
    # Create a EPR socket for entanglement generation
    epr_socket = EPRSocket("sender")
    
    # Initialize the connection
    receiver2 = NetQASMConnection(
        app_name=app_config.app_name, log_config=log_config, epr_sockets=[epr_socket]
    )
    
    with receiver2:
        epr2 = epr_socket.recv()[0]
        receiver2.flush()
        outcome = epr2.measure()
        receiver2.flush()

    app_logger.log(f"outcome = {outcome}")

    return {
        "measurement_outcome": int(outcome)
    }


if __name__ == "__main__":
    main()

