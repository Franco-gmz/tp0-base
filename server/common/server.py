import socket
import logging
import signal
import threading

from protocol.serializer import deserialize_bet
from protocol.message import Message, MessageType
from common.utils import has_won_bet, load_agency_bets, store_agency_bets

NOT_FINISH = False
FINISH = True

class Server:
    
    # Initializes the server socket, shared state for connected clients,
    # draw results, and the lock used to protect concurrent access.
    def __init__(self, port, listen_backlog, nclients = 5):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

        self._client_sockets = []
        self._client_status = {}     
        self._agency_by_client = {} 
        self.total_agencies = nclients

        self._draw_started = False
        self._draw_done = False
        self._winners_by_agency = {}

        self._server_running = True
        self._state_lock = threading.Lock()
        self._draw_condition = threading.Condition(self._state_lock)

        signal.signal(signal.SIGTERM, self.__handle_signal)

    # Registers a newly connected client and marks it as not finished yet.
    # Uses the shared-state lock because client status is global state.
    def __add_client(self, client):
        with self._state_lock:
            self._client_sockets.append(client)
            self._client_status[client] = NOT_FINISH

    # Removes a client from the server state and deletes its associated data.
    # Uses the shared-state lock because it modifies shared structures.
    def __remove_client(self, client):
        with self._state_lock:
            if client in self._client_sockets:
                self._client_sockets.remove(client)
            self._client_status.pop(client, None)
            self._agency_by_client.pop(client, None)

    # Closes all active client connections and removes them from server state.
    # Iterates over a copy of the client sockets list to avoid modification issues.
    # For each client:
    # - Attempts to retrieve its address (ip, port) for logging purposes.
    # - Closes the socket and logs success or failure.
    # - Ensures the client is removed from internal structures regardless of errors.
    # Does NOT use a lock directly here, but remove_client() handles synchronization.
    def __close_all_clients(self):
        for client in list(self._client_sockets):
            try:
                peername = client.getpeername()
            except OSError:
                peername = ("unknown", "unknown")

            try:
                client.close()
                logging.info(
                    "action: close_client_socket | result: success | ip: %s | port: %s",
                    peername[0], peername[1]
                )
            except OSError as e:
                logging.error(
                    "action: close_client_socket | result: fail | ip: %s | port: %s | error: %s",
                    peername[0], peername[1], e
                )
            finally:
                self.__remove_client(client)

    # Closes the listening server socket and stops the main accept loop.
    # Used when the server is shutting down.
    def __close_server(self):
        self._server_running = False
        try:
            self._server_socket.close()
            logging.info("action: close_server_socket | result: success")
        except OSError as e:
            logging.error("action: close_server_socket | result: fail | error: %s", e)

    # Handles SIGTERM by closing the server socket and all connected clients.
    # Allows the server to stop gracefully.
    def __handle_signal(self, sig, frame):
        if sig == signal.SIGTERM:
            logging.info("action: receive_signal | result: success | signal: SIGTERM")
            self.__close_server()
            self.__close_all_clients()

    # Main server loop: accepts new client connections and starts
    # one worker thread per client to process messages in parallel.
    def run(self):
        while self._server_running:
            try:
                client_sock = self.__accept_new_connection()
                self.__add_client(client_sock)

                thread = threading.Thread(
                    target=self.__handle_client_connection,
                    args=(client_sock,),
                    daemon=True
                )
                thread.start()

            except OSError as e:
                if not self._server_running:
                    break
                logging.error("action: accept_connections | result: fail | error: %s", e)

        logging.info("action: shutdown_server | result: success")

    # Handles the full lifecycle of one client connection.
    # Receives messages from that client and dispatches each one
    # to the corresponding handler based on its message type.
    def __handle_client_connection(self, client_sock):
        try:
            while True:
                msg = Message.from_socket(client_sock)
                
                if msg.type == MessageType.BET:
                    logging.info("action: recibo mensaje bet | result: success")
                    self.__handle_bet(client_sock, msg)

                elif msg.type == MessageType.FINISH_BETS:
                    logging.info("action: recibo mensaje finish_bets | result: success")
                    self.__handle_finish_bets(client_sock)

                elif msg.type == MessageType.GET_WINNERS:
                    logging.info("action: recibo mensaje get_winners | result: success")
                    self.__handle_get_winners(client_sock)

                else:
                    error_msg = Message(MessageType.ERROR)
                    client_sock.sendall(error_msg.to_bytes())

        except ConnectionError:
            pass

        finally:
            try:
                peername = client_sock.getpeername()
            except OSError:
                peername = ("unknown", "unknown")

            try:
                client_sock.close()
                logging.info(
                    "action: close_client_socket | result: success | ip: %s | port: %s",
                    peername[0], peername[1]
                )
            except OSError as e:
                logging.error(
                    "action: close_client_socket | result: fail | ip: %s | port: %s | error: %s",
                    peername[0], peername[1], e
                )
            finally:
                self.__remove_client(client_sock)

    # Processes a BET message: deserializes bets, stores them,
    # associates the client with its agency, and replies with ACK.
    def __handle_bet(self, client_sock, msg: Message):
        try:
            agency_id = msg.agency_id
            bets = [deserialize_bet(p.payload) for p in msg.payloads]

            if bets:
                with self._state_lock:
                    self.__bind_agency_id(client_sock, agency_id)

            store_agency_bets(bets,agency_id)
            logging.info("action: apuesta_recibida | result: success | cantidad: %s", msg.payload_count)

            ack_msg = Message(MessageType.ACK)
            client_sock.sendall(ack_msg.to_bytes())

        except Exception as e:
            logging.info(
                "action: apuesta_recibida | result: fail | cantidad: %s y agency: %s  y error: %s",
                msg.payload_count, agency_id, e
            )
            error_msg = Message(MessageType.ERROR)
            client_sock.sendall(error_msg.to_bytes())

    # Marks the client as finished sending bets.
    # If all agencies have finished and the draw was not executed yet,
    # this thread becomes responsible for running it once.
    def __handle_finish_bets(self, client_sock):
        must_run_draw = False

        with self._draw_condition:
            self._client_status[client_sock] = FINISH

            if (
                len(self._client_status) == self.total_agencies
                and all(self._client_status.values())
                and not self._draw_started
            ):
                self._draw_started = True
                must_run_draw = True

        if must_run_draw:
            winners_by_agency = self.__run_draw()

            with self._draw_condition:
                self._winners_by_agency = winners_by_agency
                self._draw_done = True
                self._draw_condition.notify_all()

            logging.info("action: sorteo | result: success")

    # Handles a GET_WINNERS request from a client.
    # Blocks the calling thread until the draw is completed using a condition variable.
    # - Acquires the shared lock through the condition.
    # - Waits (releasing the lock temporarily) until _draw_done becomes True.
    # - Once notified, retrieves the agency_id associated with the client.
    # - Fetches the winners list for that agency from shared state.
    # After releasing the lock, builds and sends a WINNERS_RESULTS message
    # containing the DNIs of the winning bets for that agency.
    # Only this thread is blocked; other client threads continue executing normally.
    def __handle_get_winners(self, client_sock):
        with self._draw_condition:
            while not self._draw_done:
                self._draw_condition.wait()

            agency_id = self._agency_by_client.get(client_sock)
            winners = self._winners_by_agency.get(agency_id, [])

        response = Message(MessageType.WINNERS_RESULTS)
        for dni in winners:
            response.add_payload(str(dni).encode())

        client_sock.sendall(response.to_bytes())

    # Executes the draw once all agencies have finished.
    # Loads all bets, checks which ones won, and stores winners grouped by agency.
    def __run_draw(self):
        winners_by_agency = {}

        bets = load_agency_bets()

        for bet in bets:
            if has_won_bet(bet):
                winners_by_agency.setdefault(bet.agency, []).append(bet.dni)

        return winners_by_agency

    # Blocks waiting for a new incoming client connection,
    # logs the event, and returns the accepted client socket.
    def __accept_new_connection(self):
        logging.info("action: accept_connections | result: in_progress")
        client_sock, addr = self._server_socket.accept()
        logging.info(
            "action: accept_connections | result: success | ip: %s | port: %s",
            addr[0], addr[1]
        )
        return client_sock
    
    # Link a client socket to its agency id
    def __bind_agency_id(self, client_sock, agency_id):
        if client_sock not in self._agency_by_client:
            self._agency_by_client[client_sock] = agency_id