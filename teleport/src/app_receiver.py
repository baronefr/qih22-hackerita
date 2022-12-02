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
        num_exp_run = 100
        m_bob_list = []
        for i in range(num_exp_run):
            epr = epr_socket.recv_keep()[0]

            m_bob = epr.measure(inplace = False)
            receiver.flush()

            m_bob_list.append(int(m_bob))

        # print(f'--> m_bob_list: {m_bob_list}')

        app_logger.log(f'm_bob_list: {m_bob_list}')
        print(f'sender measured the following (m_bob_list): {m_bob_list}')

        # Get sender the measurements
        m_alice_list = socket.recv_structured().payload
        print(f'classical receiver measures m_alice_list: {m_alice_list}')

    return {"m_alice_list": m_alice_list, \
             "m_bob_list": m_bob_list}


if __name__ == "__main__":
    main()

