import socket
import logging
import signal
from protocol.serializer import serialize_bet, deserialize_bet
from protocol.message import Message, MessageType
from domain.agency_bet import AgencyBet
from common.utils import Bet, store_agency_bets

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
        try:
            while True:
                msg = Message.from_socket(client_sock)

                if msg.type != MessageType.BET:
                    logging.info("action: apuesta_recibida | result: fail | cantidad: 0")

                    error_msg = Message(MessageType.ERROR)
                    client_sock.sendall(error_msg.to_bytes())
                    continue

                try:
                    bets = [deserialize_bet(p.payload) for p in msg.payloads]
                    store_agency_bets(bets)

                    logging.info("action: apuesta_recibida | result: success | cantidad: %s", msg.payload_count)
                    ack_msg = Message(MessageType.ACK)
                    client_sock.sendall(ack_msg.to_bytes())

                except Exception:
                    logging.info("action: apuesta_recibida | result: fail | cantidad: %s", msg.payload_count)

                    error_msg = Message(MessageType.ERROR)
                    client_sock.sendall(error_msg.to_bytes())

        except ConnectionError:
            # Client closes connection gracefully
            pass

        finally:
            try:
                peername = client_sock.getpeername()
            except OSError:
                peername = ("unknown", "unknown")

            try:
                client_sock.close()
                logging.info("action: close_client_socket | result: success | ip: %s | port: %s", peername[0], peername[1])
            except OSError as e:
                logging.error("action: close_client_socket | result: fail | ip: %s | port: %s | error: %s", peername[0], peername[1], e)
            finally:
                if client_sock in self._client_sockets:
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
