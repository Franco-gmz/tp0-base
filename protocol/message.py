from enum import Enum
from utils.socket_utils import recv_exact

class MessageType(Enum):
    BET = 1
    ACK = 2
    ERROR = 3

MAX_SIZE = 65535

class Message:
    def __init__(self, msg_type: MessageType, payload: bytes):
        self.type = msg_type
        self.payload = payload

    def to_bytes(self) -> bytes:
        payload_length = len(self.payload)

        if payload_length > MAX_SIZE:
            raise ValueError("Payload too large")

        type_bytes = self.type.value.to_bytes(1, byteorder="big")
        length_bytes = payload_length.to_bytes(2, byteorder="big")

        return type_bytes + length_bytes + self.payload

    def from_bytes(self, message):
        return
    
    @classmethod
    def from_socket(cls, sock):
        try:
            header = recv_exact(sock, 3)
            msg_type = MessageType(header[0])
            payload_length = int.from_bytes(header[1:3], "big")
            payload = recv_exact(sock, payload_length)
            return cls(msg_type, payload)
        except:
            raise ValueError("Error receiving message from socket")
        
