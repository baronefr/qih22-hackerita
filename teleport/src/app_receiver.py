import numpy as np

#**************************POKE**************************
from netqasm.logging.output import get_new_app_logger
#********************************************************

from netqasm.sdk import EPRSocket, Qubit
from netqasm.sdk.external import NetQASMConnection, Socket, get_qubit_state
from netqasm.sdk.toolbox.sim_states import get_fidelity, qubit_from, to_dm
from netqasm.sdk.toolbox import set_qubit_state

def msg_upack(x_str):
    """"""
    x_list = []
    for x in x_str:
        x_list.append(x)

    return x_list

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
    receiver = NetQASMConnection(app_name=app_config.app_name, log_config=log_config, epr_sockets=[epr_socket], min_fidelity=int(78))

    with receiver:
        num_exp_run = 100

        epr_rnd_choice = 0 #0 attack, 1 entangled

        rnd_base_choice_arr = np.random.randint(0, 2, num_exp_run)

        m_bob_list = []
        basis_bob_list = []
        for i, rnd_base_choice in zip(range(num_exp_run), rnd_base_choice_arr):
            # epr = epr_socket.recv_keep()[0]

            if epr_rnd_choice == 0:
                epr = Qubit(receiver)
                set_qubit_state(epr, 0.0, 0.0)
                receiver.flush()
            if epr_rnd_choice == 1:
                epr = epr_socket.recv_keep()[0]
                receiver.flush()

            if rnd_base_choice == 0:
                basis_bob_list.append('+')
                m_bob = epr.measure()
                receiver.flush()
            if rnd_base_choice == 1:
                basis_bob_list.append('x')
                epr.H()
                m_bob = epr.measure()
                receiver.flush()

            # m_bob_list.append((m_bob[0], int(m_bob[1])))
            m_bob_list.append(int(m_bob))

        # print(f'--> m_bob_list: {m_bob_list}')

        app_logger.log(f'm_bob_list: {m_bob_list}')
        app_logger.log(f"basis_bob_list: {basis_bob_list}")
        print(f'sender measured the following (m_bob_list): {m_bob_list}')

        # Get sender the measurements
        m_alice_str = socket.recv()
        m_alice_list = msg_upack(m_alice_str)
        print(f'classical receiver measures m_alice_list: {m_alice_list}')

    return {"m_alice_list": m_alice_list, \
             "m_bob_list": m_bob_list}


if __name__ == "__main__":
    main()

