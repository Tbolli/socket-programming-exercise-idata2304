import socket
from SmartTvLogic import SmartTV
from helpers.ProtocolConfig import Protocol
from helpers.Colors import Colors
from transport.BaseTransport import BaseTransport
from transport.TcpTransport import TcpTransport
from transport.UdpTransport import UdpTransport


class SmartTVServer:
    """TCP Server that allows clients to control a SmartTV instance."""

    BUFFER_SIZE = 128

    def __init__(self, transport: BaseTransport, available_channels: int):
        self.smart_tv = SmartTV(available_channels)
        self.transport = transport
        self.dispatch_map = {
            Protocol.COMMANDS["TURN_ON"]: self.handle_turn_on,
            Protocol.COMMANDS["TURN_OFF"]: self.handle_turn_off,
            Protocol.COMMANDS["STATUS"]: self.handle_status,
            Protocol.COMMANDS["CHANNEL_TOTAL"]: self.handle_channel_total,
            Protocol.COMMANDS["CHANNEL_ACTIVE"]: self.handle_channel_active,
            Protocol.COMMANDS["CHANNEL_SET"]: self.handle_channel_set,
            Protocol.COMMANDS["CHANNEL_DOWN"]: self.handle_channel_down,
            Protocol.COMMANDS["CHANNEL_UP"]: self.handle_channel_up,
            Protocol.COMMANDS["QUIT"]: self.handle_quit,
        }

    def start(self):
       self.transport.start()

    def handle_client(self, conn: socket.socket):
        """Handle requests from a single client until it disconnects."""
        try:
            while True:
                data = conn.recv(self.BUFFER_SIZE)
                if not data:
                    print("Client disconnected")
                    break

                command_parts = data.decode(errors="ignore").strip().lower().split()
                if not command_parts:
                    self.send_response(conn, "Invalid command")
                    continue

                # Try to match the longest possible command
                for length in range(len(command_parts), 0, -1):
                    candidate = " ".join(command_parts[:length])
                    handler = self.dispatch_map.get(candidate)
                    if handler:
                        should_break = handler(conn, command_parts[length:])
                        if should_break:  # quit handler can signal disconnect
                            return
                        break
                else:
                    self.handle_unsupported(conn)

        except Exception as e:
            print(Colors.colorize(f"Error handling client: {e}", False))
    
    # Handlers
    def handle_turn_on(self, conn, _):
        success, msg = self.smart_tv.turnOn()
        self.send_response(conn, Colors.colorize(msg, success))

    def handle_turn_off(self, conn, _):
        success, msg = self.smart_tv.turnOff()
        self.send_response(conn, Colors.colorize(msg, success))

    def handle_status(self, conn, _):
        state = "on" if self.smart_tv.is_on else "off"
        self.send_response(conn, f"Smart TV is {state}")

    def handle_channel_total(self, conn, _):
        success, msg = self.smart_tv.getNumberOfChannels()
        self.send_response(conn, Colors.colorize(msg, success))

    def handle_channel_active(self, conn, _):
        success, msg = self.smart_tv.getChannel()
        self.send_response(conn, Colors.colorize(msg, success))

    def handle_channel_set(self, conn, args):
        if not args:
            self.send_response(conn, f"Usage: {Protocol.COMMANDS['CHANNEL_SET']} <#int>")
            return
        try:
            new_channel = int(args[0])
        except ValueError:
            self.send_response(conn, Colors.colorize("Channel must be an integer", False))
            return
        success, msg = self.smart_tv.setChannel(new_channel)
        self.send_response(conn, Colors.colorize(msg, success))

    def handle_channel_down(self, conn, _):
        success, msg = self.smart_tv.downChannel()
        self.send_response(conn, Colors.colorize(msg, success))

    def handle_channel_up(self, conn, _):
        success, msg = self.smart_tv.upChannel()
        self.send_response(conn, Colors.colorize(msg, success))

    def handle_quit(self, conn, _):
        msg = "Connection closed by client request"
        print(Colors.colorize(msg, False))
        self.send_response(conn, msg)
        return True  # signal to close client connection

    def handle_unsupported(self, conn: socket.socket):
        """Handle unsupported commands."""
        msg = "Unsupported command received"
        print(Colors.colorize(msg, False))
        self.send_response(conn, Colors.colorize(msg, False))

    @staticmethod
    def send_response(conn: socket.socket, message: str):
        """Send a message to the client."""
        conn.send(message)

    def shutdown(self):
        """Shutdown the server socket gracefully."""
        print("Shutting down server...")
        self.server_socket.close()


if __name__ == "__main__":
    host, port = "127.0.0.1", 65432

    # Switch between TCP and UDP here
    # transport = TcpTransport(host, port, server)
    # transport = UcpTransport(host, port, server)
    transport = UdpTransport(host, port, None)
    available_channels = 120

    server = SmartTVServer(transport, available_channels)
    server.transport.server = server  # inject back-reference
    server.start()
