import globals

import socket

from server.start_server import start_server


def server_thread(_):
    """_summary_

    Args:
        _ (_type_): _description_

    Returns:
        null: simple thread with no returns
    """
    host = socket.gethostname()  # get local machine name
    port = 9090  # > 1024 $$ <65535 range
    server_name = "GW Server"

    start_server(host, port, server_name, globals.WC_DATA_IN_ROOT, globals.WC_DATA_IN_USER)
