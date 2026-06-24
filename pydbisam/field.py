import datetime
import struct
from enum import Enum, unique


@unique
class FieldType(int, Enum):
    """
    FieldType maps known DBISAM types to a Python enumeration.

    `_value_` is the type id
    `size` is the type size (for static types, 0 for string sizes which are
    defined the DBISAM column info, -1 for blob-like types, -2 for fixed-length
    strings that use exactly col_size)
    """

    STRING = (1, 0)
    DATE = (2, 4)
    BLOB = (3, -1)
    BOOLEAN = (4, 1)
    SHORT_INTEGER = (5, 2)
    INTEGER = (6, 4)
    FLOAT = (7, 8)
    TIME = (10, 4)            # millisecondi dalla mezzanotte (4 byte unsigned)
    TIMESTAMP = (11, 8)
    AUTOINC_LARGE = (18, 8)   # intero a 8 byte unsigned (AutoInc grande)
    CURRENCY = (5383, 8)
    BCD = (5635, 8)
    GRAPHIC = (6659, -1)      # memo graphic (puntatore esterno)
    AUTOINCREMET = (7430, 4)
    FIXEDCHAR = (7937, -2)    # stringa a lunghezza fissa (dimensione = col_size)

    def __new__(cls, type_id, size):
        obj = int.__new__(cls, type_id)
        obj._value_ = type_id
        obj._size = size
        return obj

    def get_size(self, col_size):
        if self._size == -1:               # BLOB / GRAPHIC (nessun dato inline)
            return 0
        elif self._size == -2:             # FIXEDCHAR (esattamente col_size byte)
            return col_size
        elif self._value_ == FieldType.AUTOINCREMET:
            return 4
        elif self._size and col_size:
            raise TypeError("Both innate size and col_size were provided.")
        elif self._size and not col_size:
            return self._size
        elif self._size == 0 and col_size:
            # Add 2 for leading \x01 and trailing \x00
            return col_size + 1
        else:
            raise TypeError("Neither innate size nor col_size were provided.")


class _UnknownFieldType:
    """Rappresenta un tipo di campo non mappato nell'enumerazione FieldType."""
    def __init__(self, typeid, col_size):
        self._value_ = typeid
        self._size = col_size

    def get_size(self, col_size):
        return col_size

    def __str__(self):
        return f"UnknownType({self._value_})"


class Field:
    """
    Field stores the field structure and decodes data from row data
    """

    def __init__(self, typeid, name, index, col_size, col_offset):
        self._name = name
        self._index = index
        self._row_offset = col_offset

        # Try to map the type id to a known FieldType
        try:
            self._type = FieldType(typeid)
        except ValueError:
            # Unknown type → placeholder that preserves the real byte size
            self._type = _UnknownFieldType(typeid, col_size)

        self._size = self._type.get_size(col_size)

    def __str__(self):
        return str(self._type)

    @property
    def type(self):
        return self._type

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return self._size

    @property
    def index(self):
        return self._index

    @property
    def row_offset(self):
        return self._row_offset

    @property
    def is_unknown_type(self):
        """True if the field type is not in the FieldType enum."""
        return isinstance(self._type, _UnknownFieldType)

    @property
    def is_exportable(self):
        """
        Returns False for field types that should not appear in a CSV export
        (BLOBs, memo graphics, etc.).
        """
        # Add other non-exportable types here
        non_exportable = (FieldType.BLOB, FieldType.GRAPHIC)
        if self._type in non_exportable:
            return False
        return True

    def decode_from_row(self, row_data):
        field_data = row_data[self.row_offset : self.row_offset + self.size]

        # Boolean has no preceding "null" byte
        if self._type is FieldType.BOOLEAN:
            return bool(struct.unpack("<b", field_data)[0])

        # All other fields have a preceding byte that is non-zero if the
        # field has a value, zero if it's NULL.
        is_none_data = row_data[self.row_offset - 1 : self.row_offset]
        if not struct.unpack("<b", is_none_data)[0]:
            return None

        # --- BLOB-like types (no inline data) ---
        if self._type in (FieldType.BLOB, FieldType.GRAPHIC):
            return None

        # --- Fixed-length character field ---
        if self._type is FieldType.FIXEDCHAR:
            raw = bytearray(field_data)
            # Remove trailing spaces or nulls (typical for fixed char)
            return raw.decode("cp1252", errors="replace").rstrip("\x00 ")

        # --- Time field (milliseconds from midnight) ---
        if self._type is FieldType.TIME:
            milliseconds = struct.unpack("<I", field_data)[0]
            if milliseconds >= 24 * 3600 * 1000:   # value out of range
                return None
            h = milliseconds // 3_600_000
            m = (milliseconds % 3_600_000) // 60_000
            s = (milliseconds % 60_000) / 1000.0
            return datetime.time(h, m, int(s), int((s % 1) * 1_000_000))

        # --- Regular types ---
        if self._type is FieldType.STRING:
            return (
                bytearray(field_data).decode("cp1252", errors="replace").rstrip("\x00")
            )
        elif self._type is FieldType.DATE:
            days = struct.unpack("<i", field_data)[0]
            if days == 0:
                return None
            return datetime.date(1, 1, 1) + datetime.timedelta(days - 1)
        elif self._type is FieldType.SHORT_INTEGER:
            return struct.unpack("<h", field_data)[0]
        elif self._type is FieldType.INTEGER:
            return struct.unpack("<i", field_data)[0]
        elif self._type is FieldType.FLOAT:
            return struct.unpack("<d", field_data)[0]
        elif self._type is FieldType.TIMESTAMP:
            milliseconds = struct.unpack("<d", field_data)[0]
            if milliseconds < 24 * 60 * 60 * 1000:
                return None
            ts = datetime.datetime(1, 1, 1)
            ts += datetime.timedelta(milliseconds=milliseconds)
            ts -= datetime.timedelta(days=1)
            return ts
        elif self._type in (FieldType.CURRENCY, FieldType.BCD):
            return struct.unpack("<d", field_data)[0]
        elif self._type is FieldType.AUTOINCREMET:
            return struct.unpack("<I", field_data)[0]
        elif self._type is FieldType.AUTOINC_LARGE:
            return struct.unpack("<Q", field_data)[0]
        else:
            # Unknown types → return None for safety
            return None


if __name__ == "__main__":
    print("Test FieldType enum")
    print(FieldType(1))
    print(FieldType(6)._size)

    print("Test Field class")
    x = Field(1, "Test", 8, 1, 0)
    print(x)
