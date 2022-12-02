import numpy as np

import math

from netqasm.logging.output import get_new_app_logger
from netqasm.sdk import EPRSocket, Qubit
from netqasm.sdk.classical_communication.message import StructuredMessage
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk.toolbox import set_qubit_state

#**************************POKE**************************
#********************************************************
def msg_pack(x_list):
    """"""
    x_str = ''
    for x in x_list:
        x_str = x_str+str(x)

    return x_str

def main(app_config=None, phi=0.0, theta=0.0):

    log_config = app_config.log_config

    app_logger = get_new_app_logger(app_name="sender", log_config=log_config)

    # Create a socket to send classical information
    socket = Socket("sender", "receiver", log_config=log_config)

    # Create a EPR socket for entanglement generation
    epr_socket = EPRSocket("receiver")

    print("`sender` will start to teleport a qubit to `receiver`")

    # Initialize the connection to the backend
    sender = NetQASMConnection(app_name=app_config.app_name, log_config=log_config, epr_sockets=[epr_socket])

    with sender:
        num_exp_run = 1000

        rnd_base_choice_arr = np.random.randint(0, 2, num_exp_run)

        m_alice_list = []
        basis_alice_list = []
        for i, rnd_base_choice in zip(range(num_exp_run), rnd_base_choice_arr):
            epr = epr_socket.create_keep()[0]

            if rnd_base_choice == 0:
                basis_alice_list.append('+')
                m_alice = epr.measure()
            if rnd_base_choice == 1:
                basis_alice_list.append('x')
                epr.H()
                m_alice = epr.measure()
            sender.flush()

            # m_alice_list.append((m_alice[0], int(m_alice[1])))
            m_alice_list.append(int(m_alice))

        # print(f'--> m_alice_list: {m_alice_list}')

    app_logger.log(f"m_alice_list: {m_alice_list}")
    app_logger.log(f"basis_alice_list: {basis_alice_list}")
    print(f"`sender` measured the following (m_alice_list): {m_alice_list}")

    print("`sender` will send the corrections to `receiver`")
    # socket.send_structured(StructuredMessage("Corrections", (m_alice_list)))
    
    tmp_msg = msg_pack(m_alice_list)
    socket.send(tmp_msg)

    return {"m_alice_list": m_alice_list, \
            "basis_alice_list": basis_alice_list}


if __name__ == "__main__":
    main()