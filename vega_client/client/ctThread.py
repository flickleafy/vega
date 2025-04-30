from client.client_connection import connect_to_server
import globals

import socket

from vega_common.utils.logging_utils import get_module_logger

# Setup module-specific logging
logger = get_module_logger("vega_client/client")


def client_thread(_):
    """_summary_

    Args:
        _ (_type_): _description_

    Returns:
        null: simple thread with no returns
    """
    host = socket.gethostname()  # get local machine name
    port = 9090  # > 1024 $$ <65535 range

    logger.info("Appindicator client Started")

    connect_to_server(host, port, "gateway", globals.WC_DATA)
