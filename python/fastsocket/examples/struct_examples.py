from fastsocket import (
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


class Numbers(Struct):
    a: i8  # signed char
    b: u8  # unsigned char
    c: i16  # signed short
    d: u16  # unsigned short
    e: i32  # signed int
    f: u32  # unsigned int
    g: i64  # signed long long
    h: u64  # unsigned long long
    i: f32  # float
    j: f64  # double
    k: bool  # one byte bool
    m: byte  # unsigned char
    n: rune  # signed int


class Iterables(Struct):
    a: str  # length-prefixed string
    b: list[u8]  # length-prefixed list


class Other(Struct):
    default_value: u8 = u8(0x20)
    empty_string: str = ""  # takes one byte
    empty_list_of_strings: list[str] = []  # takes one byte


numbers = Numbers(
    a=-1,
    b=255,
    c=-12345,
    d=54321,
    e=-123456789,
    f=123456789,
    g=-1234567890123456789,
    h=1234567890123456789,
    i=3.14,
    j=2.718281828,
    k=True,
    m=255,
    n=65,
)

iterables = Iterables(
    a="hello",
    b=[1, 2, 3, 4, 5],
)

other = Other(empty_string="a")  # all defaults

for x in (numbers, iterables, other):
    print_hex(x)
