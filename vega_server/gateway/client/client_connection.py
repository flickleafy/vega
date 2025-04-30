import time
import socket
import json
import errno
from vega_common.utils.datetime_utils import get_current_time
from vega_common.utils.logging_utils import get_module_logger

# Setup module-specific logging
logger = get_module_logger("vega_server/gateway/client")


def data_reception_loop(client_socket, server_name, received_data):
    """
    The inner loop for data reception

    Args:
        client_socket (socket): The client socket object.
        received_data (dict): A reference memory to store received data.
    """
    while True:
        try:
            client_socket.sendall("1".encode("utf-8"))

            json_data_in = client_socket.recv(1024)
            json_data_in = json_data_in.decode("utf-8")

            received_data[0] = json.loads(json_data_in)
            logger.info(
                f"{get_current_time()}Received from {server_name} server: {received_data[0]}"
            )
        except Exception as e:
            logger.error(f"An exception occurred: {e}")
            return False
        time.sleep(3)


def connect_to_server(address, port, server_name, received_data):
    """
    Connect to the server at the given address and port, and send data.

    Args:
        address (str): The server's IP address or hostname.
        port (int): The port number to connect to.
        received_data (list): A reference memory to store received data.
    """
    while True:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Non-blocking mode
        client_socket.settimeout(1.0)

        try:
            client_socket.connect((address, port))

            # Restore to blocking mode after successful connection
            client_socket.settimeout(None)

            if not data_reception_loop(client_socket, server_name, received_data):
                client_socket.close()

        except socket.timeout:
            logger.warning(f"Server at {address}:{port} is not running. Trying to reconnect...")
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED:
                logger.warning(
                    f"Connection refused by the server at {address}:{port}. Trying to reconnect..."
                )
            else:
                logger.error(f"An error occurred: {e}. Trying to reconnect...")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}. Trying to reconnect...")

        # Close the client socket to avoid port blocking
        client_socket.close()

        time.sleep(3)  # Sleep for 3 seconds before trying to reconnect
