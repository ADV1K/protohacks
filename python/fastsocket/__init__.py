"""FastSocket: build network servers, just like that. Based on Python type hints."""

from .main import FastTCP
from .struct import (
    Struct,
    byte,
    f32,
    f64,
    i8,
    i16,
    i32,
    i64,
    print_hex,
    rune,
    u8,
    u16,
    u32,
    u64,
)
from .utils import get_ip, get_public_ip
