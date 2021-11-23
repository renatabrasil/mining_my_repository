import socket


def get_server_type():
    return socket.gethostname()
