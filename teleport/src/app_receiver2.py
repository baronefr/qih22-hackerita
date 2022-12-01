from netqasm.sdk import EPRSocket
from netqasm.sdk.external import NetQASMConnection, Socket, get_qubit_state
from netqasm.sdk.toolbox.sim_states import get_fidelity, qubit_from, to_dm


def main(app_config=None):
    if(False):
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
            epr = epr_socket.recv()[0]
            receiver2.flush()

            # Get the corrections
            m1, m2 = socket.recv_structured().payload
            print(f"`receiver2` got corrections: {m1}, {m2}")
            if m2 == 1:
                print("`receiver2` will perform X correction")
                epr.X()
            if m1 == 1:
                print("`receiver2` will perform Z correction")
                epr.Z()

            receiver2.flush()
            # Get the qubit state
            # NOTE only possible in simulation, not part of actual application
            dm = get_qubit_state(epr)
            print(f"`receiver2` recieved the teleported state {dm}")

            # Reconstruct the original qubit to compare with the received one
            # NOTE only to check simulation results, normally the Sender does not
            # need to send the phi and theta values!
            msg = socket.recv_silent()  # don't log this
            phi, theta = eval(msg)

            original = qubit_from(phi, theta)
            original_dm = to_dm(original)
            fidelity = get_fidelity(original, dm)

            return {
                "original_state": original_dm.tolist(),
                "correction1": "Z" if m1 == 1 else "None",
                "correction2": "X" if m2 == 1 else "None",
                "received_state": dm.tolist(),
                "fidelity": fidelity,
            }

    return


if __name__ == "__main__":
    main()

