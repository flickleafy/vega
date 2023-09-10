import socket
import time

import json
from utils.datetime import get_current_time


def start_server(address, port, server_name, send_data_1, send_data_2):
    """
    Start the server and listen for incoming connections.

    Args:
        address (str): The server's IP address or hostname.
        port (int): The port number to connect to.
        send_data (dict): A reference memory to store send data.
    """
    while True:
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                server_socket.bind((address, port))
            except Exception as e:
                server_socket.close()
                print(f"An error occurred: {e}")

            server_socket.listen(1)
            print(server_name, ' started. Waiting for connections...')

            connection, addr = server_socket.accept()
            print(f"Connection from {address}")

            if not data_transfer_loop(connection, send_data_1, send_data_2):
                connection.close()

        except Exception as e:
            print(f"An error occurred: {e}")

        time.sleep(3)  # Sleep for 3 seconds before trying to restart


def data_transfer_loop(connection, send_data_1, send_data_2):
    """
    Handle data transfer for the connection.
    """
    while True:
        try:
            json_data_in = connection.recv(1024)
            if not json_data_in:
                print("Connection lost. Trying to reconnect...")
                return False

            json_data_in = json_data_in.decode('utf-8')
            json_data_out = json.dumps({**send_data_1[0], **send_data_2[0]})
            print(get_current_time() +
                  "Sending to gateway server: ", str(json_data_out))
            connection.sendall(str(json_data_out).encode('utf-8'))
        except Exception as e:
            print(f"An error occurred in data transfer: {e}")
            return False
        time.sleep(3)
