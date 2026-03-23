from dataclasses import dataclass

@dataclass
class Payload:
    payload: bytes

    @property
    def size(self) -> int:
        return len(self.payload)