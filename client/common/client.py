import logging
import socket
import signal
import os

from domain.agency_bet import AgencyBet
from protocol.serializer import serialize_bet
from protocol.message import Message, MessageType
from utils.file_utils import iter_csv_rows

log = logging.getLogger("log")

class ClientConfig:
    def __init__(self, client_id, server_address, loop_amount, loop_period, max_amount):
        self.ID = client_id
        self.ServerAddress = server_address
        self.LoopAmount = loop_amount
        self.LoopPeriod = loop_period
        self.max_amount = max_amount

class Client:
    def __init__(self, config: ClientConfig):
        self.config = config
        self.conn = None
        self._shutting_down = False
        signal.signal(signal.SIGTERM, self.__handle_signal)

    def __create_client_socket(self):
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

    def __handle_signal(self, sig, frame):
        if sig == signal.SIGTERM:
            log.info("action: receive_signal | result: success | signal: SIGTERM")
            self._shutting_down = True
            if self.conn:
                self.conn.close()

    def start_client_loop(self):
        if self._shutting_down:
            return

        err = self.__create_client_socket()
        if err:
            return

        try:
            batches = self.__build_batches()
            for batch in batches:
                self.__send_batch(batch)
                result = self.__recv_result()
                self.__log_result(result, batch)
            self.__notify_without_payload(MessageType.FINISH_BETS)
            self.__notify_without_payload(MessageType.GET_WINNERS)
            results = self.__recv_result()
            self.__log_winners_result(results)
        except Exception as err:
            if self._shutting_down:
                return
            log.error("action: receive_message | result: fail | client_id: %s | error: %s", self.config.ID, err)
            return
        finally:
            if self.conn:
                try:
                    self.conn.close()
                except Exception:
                    pass
                self.conn = None

            if self._shutting_down:
                return
    
    def __build_batches(self):
        batches = []
        message = Message(MessageType.BET, self.config.ID)

        for bet in self.__iter_agency_bets():
            bet_bytes = serialize_bet(bet)

            if message.payload_count == self.config.max_amount:
                batches.append(message)
                message = Message(MessageType.BET, self.config.ID)

            message.add_payload(bet_bytes)

        if message.payload_count > 0:
            batches.append(message)
        return batches


    def __send_batch(self, batch: Message):
        self.conn.sendall(batch.to_bytes())

    def __recv_result(self) -> Message:
        return Message.from_socket(self.conn)
    
    def __notify_without_payload(self, msg_type: MessageType):
        notification = Message(msg_type, self.config.ID)
        self.conn.sendall(notification.to_bytes())
    
    def __log_result(self, result: Message, batch: Message) -> None:
        if result.type == MessageType.ACK:
            log.info("action: batch_enviado | result: success | cantidad: %s", batch.payload_count)
        elif result.type == MessageType.ERROR:
            log.info("action: batch_enviado | result: fail | cantidad: %s", batch.payload_count)
        else:
            log.info("action: batch_enviado | result: unknown")

    def __log_winners_result(self, result: Message) -> None:
        if result.type == MessageType.WINNERS_RESULTS:
            log.info("action: consulta_ganadores | result: success | cant_ganadores: %s", result.payload_count)
        elif result.type == MessageType.ERROR:
            log.info("action: consulta_ganadores | result: fail")
        else:
            log.info("action: consulta_ganadores | result: unknown")

    def __iter_agency_bets(self):
        path = os.getenv("BATCH_FILE")

        for row in iter_csv_rows(path):
            yield AgencyBet.from_row(row)