import socket
import time
import threading
import json
from vega_common.utils.datetime_utils import get_current_time
from vega_common.utils.logging_utils import get_module_logger

# Setup module-specific logging
logger = get_module_logger("vega_server/gateway/server")


def start_server(address, port, server_name, send_data_1, send_data_2):
    """
    Start the server and listen for incoming connections.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((address, port))
        server_socket.listen()
        logger.info(f"{server_name} started. Waiting for connections...")
        while True:
            try:
                connection, addr = server_socket.accept()
                logger.info(f"Connection from {addr}")
                client_thread = threading.Thread(
                    target=handle_client, args=(connection, send_data_1, send_data_2)
                )
                client_thread.start()
            except Exception as e:
                logger.error(f"An error occurred with a client: {e}")
    except Exception as e:
        logger.error(f"An error occurred while starting the server: {e}")
    finally:
        server_socket.close()


def handle_client(connection, send_data_1, send_data_2):
    """
    Handle the client connection.
    """
    try:
        if not data_transfer_loop(connection, send_data_1, send_data_2):
            connection.close()
    except Exception as e:
        logger.error(f"An error occurred with the connection: {e}")
        connection.close()


def data_transfer_loop(connection, send_data_1, send_data_2):
    """
    Handle data transfer for the connection.
    """
    while True:
        try:
            json_data_in = connection.recv(1024)
            if not json_data_in:
                logger.warning("Connection lost. Trying to reconnect...")
                return False

            json_data_in = json_data_in.decode("utf-8")
            json_data_out = json.dumps({**send_data_1[0], **send_data_2[0]})
            logger.debug(f"{get_current_time()}Sending to gateway server: {json_data_out}")
            connection.sendall(str(json_data_out).encode("utf-8"))
        except Exception as e:
            logger.error(f"An error occurred in data transfer: {e}")
            return False
        time.sleep(3)
