#**************************POKE**************************
from netqasm.logging.output import get_new_app_logger
#********************************************************

from netqasm.sdk import EPRSocket
from netqasm.sdk.external import NetQASMConnection, Socket, get_qubit_state
from netqasm.sdk.toolbox.sim_states import get_fidelity, qubit_from, to_dm


def main(app_config=None):
    log_config = app_config.log_config

    #**************************POKE**************************
    app_logger = get_new_app_logger(app_name="receiver", log_config=log_config)
    #********************************************************

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

        #Measure EPR state
        m1_bob = epr.measure(inplace = True)
        app_logger.log(f'--> m1_bob: {type(m1_bob)}')

        # Get the measurements
        m1_alice = socket.recv_structured().payload

        receiver.flush()

        return {"m1_alice": m1_alice, "m1_bob": int(str(m1_bob))}


if __name__ == "__main__":
    main()

