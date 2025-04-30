from client.client_connection import connect_to_server
import globals

import socket

from vega_common.utils.logging_utils import get_module_logger

# Setup module-specific logging
logger = get_module_logger("vega_server/gateway/client")


def client_thread(_):
    """Client thread for user space data reception.

    Args:
        _ (_type_): Unused argument for thread signature consistency.

    Returns:
        null: simple thread with no returns
    """
    host = socket.gethostname()  # get local machine name
    port = 9095  # > 1024 $$ <65535 range

    logger.info("User Client Started")

    connect_to_server(host, port, "userspace", globals.WC_DATA_IN_USER)
