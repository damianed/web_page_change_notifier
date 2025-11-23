import sqlite3

class SqliteConnection:
    _instance = None
    connection = None

    def __new__(cls, db_path: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, db_path: str):
        if self.connection is None:
            self.connection = sqlite3.connect(db_path)
