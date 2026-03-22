import logging
import socket
import signal
import os

from domain.agency_bet import AgencyBet
from protocol.serializer import serialize_bet, deserialize_bet
from protocol.message import Message, MessageType

log = logging.getLogger("log")

class ClientConfig:
    def __init__(self, client_id, server_address, loop_amount, loop_period):
        self.ID = client_id
        self.ServerAddress = server_address
        self.LoopAmount = loop_amount
        self.LoopPeriod = loop_period

class Client:
    def __init__(self, config):
        self.config = config
        self.conn = None
        self._shutting_down = False
        signal.signal(signal.SIGTERM, self.handle_signal)

    def create_client_socket(self):
        try:
            host, port = self.config.ServerAddress.split(":")
            self.conn = socket.create_connection((host, int(port)))
        except Exception as err:
            log.critical(
                "action: connect | result: fail | client_id: %s | error: %s",
                self.config.ID,
                err,
            )
            return err
        return None

    def handle_signal(self, sig, frame):
        if sig == signal.SIGTERM:
            log.info("action: receive_signal | result: success | signal: SIGTERM")
            self._shutting_down = True
            if self.conn:
                self.conn.close()

    def start_client_loop(self):
        if self._shutting_down:
            return

        err = self.create_client_socket()
        if err:
            return

        try:
            agency_bet = self.build_bet()
            self.send_bet(agency_bet)
        except Exception as err:
            if self._shutting_down:
                return
            log.error("action: receive_message | result: fail | client_id: %s | error: %s", self.config.ID, err)
            return
        finally:
            if self.conn:
                try:
                    ack = self.recv_ack()
                    confirmed_bet = deserialize_bet(ack.to_bytes())

                    if ack.type == MessageType.ACK:
                        log.info(f"action: apuesta_enviada | result: success | dni: {confirmed_bet.dni} | numero: {confirmed_bet.bet_number}")
                    else:
                        log.info(f"action: apuesta_enviada | result: fail | dni: {confirmed_bet.dni} | numero: {confirmed_bet.bet_number}")
                    self.conn.close()
                except Exception:
                    pass
                self.conn = None

            if self._shutting_down:
                return


    def build_bet(self) -> AgencyBet:
        return AgencyBet(
            name=os.getenv("NOMBRE"),
            lastname=os.getenv("APELLIDO"),
            dni=os.getenv("DOCUMENTO"),
            birth_date=os.getenv("NACIMIENTO"),
            bet_number=int(os.getenv("NUMERO"))
        )

    def send_bet(self, bet: AgencyBet):
        payload = serialize_bet(bet)
        msg = Message(MessageType.BET, payload)
        self.conn.sendall(msg.to_bytes())

    def recv_ack(self) -> Message:
        return Message.from_socket(self.conn)