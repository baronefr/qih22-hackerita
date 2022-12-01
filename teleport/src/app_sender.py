import math

from netqasm.logging.output import get_new_app_logger
from netqasm.sdk import EPRSocket, Qubit
from netqasm.sdk.classical_communication.message import StructuredMessage
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk.toolbox import set_qubit_state

#**************************POKE**************************
#********************************************************

def main(app_config=None, phi=0.0, theta=0.0):

    log_config = app_config.log_config

    app_logger = get_new_app_logger(app_name="sender", log_config=log_config)

    # Create a socket to send classical information
    socket = Socket("sender", "receiver", log_config=log_config)

    # Create a EPR socket for entanglement generation
    epr_socket = EPRSocket("receiver")

    print("`sender` will start to teleport a qubit to `receiver`")

    # Initialize the connection to the backend
    sender = NetQASMConnection(
        app_name=app_config.app_name, log_config=log_config, epr_sockets=[epr_socket]
    )
    with sender:
        # Create EPR pairs
        epr = epr_socket.create()[0]

        #Measure EPR state
        m1_alice = epr.measure()

    # Send the correction information
    m1_alice= int(m1_alice)

    app_logger.log(f"mock_m1 = {m1_alice}")
    print(
        f"`sender` measured the following teleportation corrections: m1_alice = {m1_alice}"
    )
    print("`sender` will send the corrections to `receiver`")

    m2 = 0
    socket.send_structured(StructuredMessage("Corrections", (m1_alice, m2)))

    socket.send_silent(str((phi, theta)))

    return {"m1_alice": m1_alice, "m2": m2}


if __name__ == "__main__":
    main()