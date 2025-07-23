from dataclasses import dataclass

from fastsocket import BaseModel, FastTCP


@dataclass
class Message(BaseModel):
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
