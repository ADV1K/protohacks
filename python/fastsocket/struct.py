import re
import struct
from typing import Any, ClassVar, Self, Type, TypedDict, TypeVar, get_args, get_origin

T = TypeVar("T", bound="Struct")

"""
Issues:
    1. cannot decode because we don't known the length of dynamic types, to create the struct. in short, struct won't work, need manual byte decoding.
    2. list of strings doesn't work.
"""


class StructMeta(type):
    def __new__(mcs, name, bases, namespace):
        # load config class
        # config_obj: StructConfig = namespace.get("Config")
        # config = {}
        # if config_obj:
        #     config = {
        #         key: getattr(config_obj, key)
        #         for key in StructConfig.__annotations__
        #         if hasattr(config_obj, key)
        #     }
        # namespace["config"] = cast(StructConfig, config)

        annotations = namespace.get("__annotations__", {})
        model_defaults = {
            k: v
            for k, v in namespace.items()
            if not callable(v) and not k.startswith("__")
        }

        model_fields = []
        for field_name, field_type in annotations.items():
            if hasattr(field_type, "__origin__") and field_type.__origin__ is ClassVar:
                continue

            model_fields.append(field_name)

        def make_new(model_fields, model_defaults):
            def __new__(cls, **data):
                self = object.__new__(cls)
                for field in model_fields:
                    if field in data:
                        setattr(self, field, data[field])
                    elif field not in model_defaults:
                        raise TypeError(f"Missing required argument: {field}")
                return self

            return __new__

        def struct_fmt(field_name, field_type, field_value) -> str:
            # Full struct-compatible type map
            FMT_MAP = {
                i8: "b",  # signed char
                u8: "B",  # unsigned char
                i16: "h",  # signed short
                u16: "H",  # unsigned short
                i32: "i",  # signed int
                u32: "I",  # unsigned int
                i64: "q",  # signed long long
                u64: "Q",  # unsigned long long
                f32: "f",  # float
                f64: "d",  # double
                bool: "?",
                byte: "B",
                rune: "i",
            }

            if field_type in FMT_MAP:
                return FMT_MAP[field_type]

            if field_type is str:
                return f"{FMT_MAP[u8]}{len(field_value)}s"

            if get_origin(field_type) is list:
                elem_type = get_args(field_type)[0]
                if elem_type not in FMT_MAP:
                    raise TypeError(f"Unsupported type: {field_type}")
                return f"{FMT_MAP[u8]}{len(field_value)}{FMT_MAP[elem_type]}"

            raise TypeError(f"Unsupported type: {field_name} {field_type}")

        @property
        def model_struct(self: "Struct") -> struct.Struct:
            fmt = "!"
            for field_name, field_type in self.__annotations__.items():
                field_value = getattr(self, field_name)
                fmt += struct_fmt(field_name, field_type, field_value)
            return struct.Struct(fmt)

        namespace["model_fields"] = tuple(model_fields)
        namespace["model_struct"] = model_struct
        namespace["__new__"] = make_new(model_fields, model_defaults)
        # namespace["__slots__"] = tuple(
        #     f for f in model_fields if f not in model_defaults
        # )

        return super().__new__(mcs, name, bases, namespace)


class Struct(metaclass=StructMeta):
    model_fields: ClassVar[tuple[str, ...]]
    model_defaults: ClassVar[dict[str, Any]]

    def __new__(cls: type[Self], **data: Any) -> Self: ...
    @property
    def model_struct(self: Self) -> struct.Struct: ...

    def encode(self: "Struct") -> bytes:
        values = []
        for field in self.model_fields:
            val = getattr(self, field)
            if isinstance(val, str):
                values.append(len(val))
                values.append(val.encode())
            elif isinstance(val, list):
                values.append(len(val))
                values.extend(val)
            else:
                values.append(val)
        return self.model_struct.pack(*values)

    @classmethod
    def decode(cls: Type[T], data: bytes) -> T:
        s = cls().model_struct
        unpacked = s.unpack(data)

        values: dict[str, Any] = {}
        idx = 0
        for field in cls.model_fields:
            default = cls.model_defaults.get(field)
            if isinstance(default, str):
                # expect length + bytes
                _len = unpacked[idx]
                values[field] = unpacked[idx + 1][:_len].decode()
                idx += 2
            else:
                values[field] = unpacked[idx]
                idx += 1

        return cls(**values)


class StructConfig(TypedDict, total=False):
    """
    Config dict for Struct

    Attributes:
        message_type (StructValue): A custom value to prepend in front of each struct
    """

    ...
    # message_type: StructValue


class StructValue:
    pass


class i8(int, StructValue):
    pass


class i16(int, StructValue):
    pass


class i32(int, StructValue):
    pass


class i64(int, StructValue):
    pass


class u8(int, StructValue):
    pass


class u16(int, StructValue):
    pass


class u32(int, StructValue):
    pass


class u64(int, StructValue):
    pass


class f32(float, StructValue):
    pass


class f64(float, StructValue):
    pass


class byte(u8, StructValue):
    pass


class rune(i32, StructValue):
    pass


def print_hex(obj: Struct) -> None:
    def group_fmt(fmt: str) -> list[str]:
        return re.findall(r"\d*[xcbB?hHiIlLqQnNefdspP]", fmt)

    encoded = obj.encode()
    fmt = obj.model_struct.format[1:]
    offset = 0
    print(f"{obj.__class__.__name__} ({fmt}):")
    for field, fmt_char in zip(obj.model_fields, group_fmt(fmt)):
        size = struct.calcsize(fmt_char)
        field_bytes = encoded[offset : offset + size]
        print(f"  {field}: {' '.join(f'{b:02X}' for b in field_bytes)}")
        offset += size
