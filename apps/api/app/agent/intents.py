from enum import Enum


class Intent(str, Enum):
    DATABASE_READ = "database_read"
    DATABASE_WRITE_REQUEST = "database_write_request"
    SUMMARIZE_DATA = "summarize_data"
    UNKNOWN = "unknown"
