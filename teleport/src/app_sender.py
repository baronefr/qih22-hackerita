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
        m_alice_list = []
        for i in range(100):
            epr = epr_socket.create_keep()[0]

            m_alice = epr.measure()
            sender.flush()

            m_alice_list.append(int(m_alice))

        # print(f'--> m_alice_list: {m_alice_list}')

    app_logger.log(f"m_alice_list: {m_alice_list}")
    print(f"`sender` measured the following (m_alice_list): {m_alice_list}")

    print("`sender` will send the corrections to `receiver`")
    socket.send_structured(StructuredMessage("Corrections", (m_alice_list)))

    return {"m_alice_list": m_alice_list}


if __name__ == "__main__":
    main()