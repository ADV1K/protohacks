from dataclasses import dataclass

from fastsocket import FastTCP, Struct


@dataclass
class Message(Struct):
    message: str

    @classmethod
    def from_bytes(cls, data: bytes) -> "Message":
        return cls(message=data.decode())

    def to_bytes(self) -> bytes:
        return f"{self.message}\n".encode()


app = FastTCP()


@app.handler(request_delimiter=b"\n")
async def handler(request: Message) -> Message:
    return Message(request.message)


app.run()
