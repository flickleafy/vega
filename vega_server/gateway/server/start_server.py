import socket
import time
import threading
import json
from vega_common.utils.datetime_utils import get_current_time


def start_server(address, port, server_name, send_data_1, send_data_2):
    """
    Start the server and listen for incoming connections.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((address, port))
        server_socket.listen()
        print(f"{server_name} started. Waiting for connections...")
        while True:
            connection, addr = server_socket.accept()
            print(f"Connection from {addr}")
            client_thread = threading.Thread(
                target=handle_client, args=(connection, addr, send_data_1, send_data_2)
            )
            client_thread.daemon = True  # Optional: make client threads daemon threads
            client_thread.start()


def handle_client(connection, address, send_data_1, send_data_2):
    """
    Handle the client connection.
    """
    try:
        print(f"Handling client {address}")
        data_transfer_loop(connection, send_data_1, send_data_2)
    except Exception as e:
        print(f"Error handling client {address}: {e}")
    finally:
        connection.close()
        print(f"Connection with {address} closed")


def data_transfer_loop(connection, send_data_1, send_data_2):
    """
    Handle data transfer for the connection.
    """
    while True:
        json_data_in = connection.recv(1024)
        if not json_data_in:
            print("Connection lost.")
            break  # Exit loop and function, leading to thread termination

        json_data_in = json_data_in.decode("utf-8")
        json_data_out = json.dumps({**send_data_1[0], **send_data_2[0]})
        print(get_current_time() + "Sending to client: ", str(json_data_out))
        connection.sendall(json_data_out.encode("utf-8"))
        time.sleep(3)
