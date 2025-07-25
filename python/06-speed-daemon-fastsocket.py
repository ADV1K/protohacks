import asyncio
from dataclasses import dataclass
from typing import AsyncGenerator, Literal

from fastsocket import FastTCP, Struct, u8, u16, u32


# Input Message Types
class Plate(Struct):
    message_type: u8 = u8(0x20)

    plate: str
    timestamp: u32


class WantHeartbeat(Struct):
    message_type: u8 = u8(0x40)

    interval: u32


class IAmCamera(Struct):
    message_type: u8 = u8(0x80)

    road: u16
    mile: u16
    limit: u16


class IAmDispatcher(Struct):
    message_type: u8 = u8(0x81)

    numroads: u8
    roads: list[u16]  # (array of u16)


# Output Message Types
class Error(Struct):
    message_type: u8 = u8(0x10)

    msg: str


class Ticket(Struct):
    message_type: u8 = u8(0x21)

    plate: str
    road: u16
    mile1: u16
    timestamp1: u32
    mile2: u16
    timestamp2: u32
    speed: u16  # (100x miles per hour)


class Heartbeat(Struct):
    message_type: u8 = u8(0x41)

    pass


@dataclass
class Client:
    type: Literal["camera", "dispatcher"]


app = FastTCP()


@app.handler(WantHeartbeat)
async def heartbeat() -> AsyncGenerator[Heartbeat]:
    """Sends heartbeat every X seconds"""
    ...


@app.handler(Plate)
async def plate() -> Error | None:
    """Number plate observation from a speed camera. Returns Error if unknown client."""
    ...


@app.handler(IAmCamera)
async def camera() -> Error | None:
    """This client is a camera at X road Y mile with Z speed limit. Returns Error if client type is known."""
    ...


@app.handler(IAmDispatcher)
async def dispatcher() -> Error | None:
    """This client is a ticket dispatcher who handles X number of roads. Returns Error if client type is known."""
    ...


@app.parser()
async def parser(stream: asyncio.StreamReader) -> AsyncGenerator[Struct, None]:
    """Parse the stream of bytes and decode it into types we can work with."""
    yield WantHeartbeat()


if __name__ == "__main__":
    ...
    # app.run()
