from enum import Enum
import logging
from utils.socket_utils import recv_exact
from protocol.payload import Payload

class MessageType(Enum):
    BET = 1
    ACK = 2
    ERROR = 3
    FINISH_BETS = 4
    GET_WINNERS = 5
    WINNERS_RESULTS = 6

MAX_SIZE = 65535
MAX_PACKET_SIZE = 8192

LEN_TYPE_BYTES = 1
LEN_AGENCY_BYTES = 1
LEN_FIELD_BYTES = 2

HEADER_BYTES = 6

TYPE_INIT = 0
AGENCY_INIT = 1
PAYLOAD_LEN_INIT = 2
PAYLOAD_LEN_END = 4
PAYLOAD_COUNT_INIT = 4
PAYLOAD_COUNT_END = 6

NO_AGENCY = 0

class Message:
    def __init__(self, msg_type: MessageType, agency_id = None):
        self.type = msg_type
        if agency_id is not None:
            self.agency_id = agency_id
        else:
            self.agency_id = NO_AGENCY
        self.payloads = []
        self.payload_count = 0
        self.payload_len = 0

    def to_bytes(self) -> bytes:
        if not len(self.payloads) > 0 and self.type is MessageType.BET:
            raise ValueError("Payload empty")

        if self.payload_len > MAX_SIZE:
            raise ValueError("Payload exceeds protocol limit")

        if HEADER_BYTES + self.payload_len > MAX_PACKET_SIZE:
            raise ValueError("Payload exceeds 8KB limit")

        type_bytes = self.type.value.to_bytes(LEN_TYPE_BYTES, byteorder="big")
        length_bytes = self.payload_len.to_bytes(LEN_FIELD_BYTES, byteorder="big")
        count_bytes = self.payload_count.to_bytes(LEN_FIELD_BYTES, byteorder="big")
        agency_bytes = int(self.agency_id).to_bytes(LEN_AGENCY_BYTES, "big")

        buffer = type_bytes + agency_bytes + length_bytes + count_bytes

        for payload in self.payloads:
            buffer += payload.size.to_bytes(LEN_FIELD_BYTES, byteorder="big")
            buffer += payload.payload

        return buffer
    
    def add_payload(self, payload):
        new_payload = Payload(payload)

        self.payload_count +=1
        self.payloads.append(new_payload)
        self.payload_len += LEN_FIELD_BYTES + new_payload.size
        
    @classmethod
    def from_socket(cls, sock):
        try:
            header = recv_exact(sock, HEADER_BYTES)

            # logging.info("HEADER RAW: %r", header)
            # logging.info("HEADER BYTES DEC: %s", list(header))
            # logging.info("HEADER BYTES HEX: %s", header.hex())

            msg_type = MessageType(header[TYPE_INIT])
            payload_length = int.from_bytes(header[PAYLOAD_LEN_INIT:PAYLOAD_LEN_END], "big")
            payload_count = int.from_bytes(header[PAYLOAD_COUNT_INIT:PAYLOAD_COUNT_END], "big")
            agency_id = header[1]

            # logging.info(
            #     "PARSED HEADER | type: %s | agency_id: %s | payload_length: %s | payload_count: %s",
            #     msg_type,
            #     agency_id,
            #     int.from_bytes(header[PAYLOAD_LEN_INIT:PAYLOAD_LEN_END], "big"),
            #     int.from_bytes(header[PAYLOAD_COUNT_INIT:PAYLOAD_COUNT_END], "big"),
            # )
            
            msg = cls(msg_type, agency_id)
            
            if payload_length > 0:
                payload_bytes = recv_exact(sock, payload_length)
                offset = 0
                for _ in range(payload_count):
                    size = int.from_bytes(
                        payload_bytes[offset:offset + LEN_FIELD_BYTES],
                        "big"
                    )
                    offset += LEN_FIELD_BYTES

                    data = payload_bytes[offset:offset + size]
                    offset += size

                    msg.payloads.append(Payload(data))

            msg.payload_len = payload_length
            msg.payload_count = payload_count
            return msg
        except ConnectionError:
            raise
        except Exception:
            raise ValueError("Error receiving message from socket")
        
