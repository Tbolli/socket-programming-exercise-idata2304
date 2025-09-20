class BaseTransport:
    def __init__(self, host: str, port: int, server):
        self.host = host
        self.port = port
        self.server = server

    def start(self):
        raise NotImplementedError("Transport must implement start()")
