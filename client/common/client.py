import logging
import socket
import time
import signal

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
    
    def handle_signal(self, sgl, frame):
        if sgl == signal.SIGTERM:
            log.info('action: receive_signal | result: success | signal: SIGTERM')
            self.conn.close()

    import logging
import socket
import time
import signal

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
        for msg_id in range(1, self.config.LoopAmount + 1):
            if self._shutting_down:
                return

            err = self.create_client_socket()
            if err:
                return

            try:
                self.conn.sendall(
                    f"[CLIENT {self.config.ID}] Message N°{msg_id}\n".encode("utf-8")
                )

                msg = b""
                while not msg.endswith(b"\n"):
                    if self._shutting_down:
                        return
                    chunk = self.conn.recv(1)
                    if not chunk:
                        break
                    msg += chunk

            except Exception as err:
                if self._shutting_down:
                    return
                log.error(
                    "action: receive_message | result: fail | client_id: %s | error: %s",
                    self.config.ID,
                    err,
                )
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

            if not msg.endswith(b"\n"):
                log.error(
                    "action: receive_message | result: fail | client_id: %s | error: connection closed before newline",
                    self.config.ID,
                )
                return

            decoded_msg = msg.decode("utf-8")

            log.info(
                "action: receive_message | result: success | client_id: %s | msg: %s",
                self.config.ID,
                decoded_msg,
            )

            slept = 0.0
            step = 0.1
            while slept < self.config.LoopPeriod:
                if self._shutting_down:
                    return
                remaining = self.config.LoopPeriod - slept
                time.sleep(step if remaining > step else remaining)
                slept += step if remaining > step else remaining

        log.info(
            "action: loop_finished | result: success | client_id: %s",
            self.config.ID,
        )