from client.client_connection import connect_to_server
import globals

import socket


def client_thread(_):
    """_summary_

    Args:
        _ (_type_): _description_

    Returns:
        null: simple thread with no returns
    """
    host = socket.gethostname()   # get local machine name
    port = 9090  # > 1024 $$ <65535 range

    print("Appindicator client Started")

    connect_to_server(host, port, 'gateway', globals.WC_DATA)
