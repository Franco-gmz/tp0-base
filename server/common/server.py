import socket
import logging
import signal

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

        #Initialize client sockets
        self._client_sockets = []

        #Signal handler
        self._server_running = True
        signal.signal(signal.SIGTERM, self.handle_signal)

    def add_client(self, client):
        self._client_sockets.append(client)

    def remove_client(self, client):
        self._client_sockets.remove(client)

    def close_all_clients(self):
        for client in list(self._client_sockets):
            try:
                peername = client.getpeername()
            except OSError:
                peername = ("unknown", "unknown")

            try:
                client.close()
                logging.info(f'action: close_client_socket | result: success | ip: {peername[0]} | port: {peername[1]}')
            except OSError as e:
                logging.error(f'action: close_client_socket | result: fail | ip: {peername[0]} | port: {peername[1]} | error: {e}')
            finally:
                self.remove_client(client)
    
    def close_server(self):
        self._server_running = False
        try:
            self._server_socket.close()
            logging.info('action: close_server_socket | result: success')
        except OSError as e:
            logging.error(f'action: close_server_socket | result: fail | error: {e}')

    def handle_signal(self, sgl, frame):
        if sgl == signal.SIGTERM:
            logging.info('action: receive_signal | result: success | signal: SIGTERM')
            self.close_server()
            self.close_all_clients()

    def handle_signal(self, sgl, frame):
        if (sgl == signal.SIGTERM):
            self.close_server()
            self.close_all_clients()
                
    def run(self):
        """
        Dummy Server loop Server that accept a new connections and establishes a communication with a client.
        After client with communucation finishes, servers starts to accept new connections again
        """
        while self._server_running:
            try:
                client_sock = self.__accept_new_connection()
                self.add_client(client_sock)
                self.__handle_client_connection(client_sock)
            except OSError as e:
                if not self._server_running:
                    break
                logging.error(f'action: accept_connections | result: fail | error: {e}')

        logging.info('action: shutdown_server | result: success')

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            msg = client_sock.recv(1024).rstrip().decode('utf-8')
            addr = client_sock.getpeername()
            logging.info(
                f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}'
            )
            client_sock.send(f"{msg}\n".encode('utf-8'))

        except OSError as e:
            logging.error(f'action: receive_message | result: fail | error: {e}')

        finally:
            try:
                peername = client_sock.getpeername()
            except OSError:
                peername = ("unknown", "unknown")

            try:
                client_sock.close()
                logging.info(
                    f'action: close_client_socket | result: success | ip: {peername[0]} | port: {peername[1]}'
                )
            except OSError as e:
                logging.error(
                    f'action: close_client_socket | result: fail | ip: {peername[0]} | port: {peername[1]} | error: {e}'
                )
            finally:
                self.remove_client(client_sock)

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
