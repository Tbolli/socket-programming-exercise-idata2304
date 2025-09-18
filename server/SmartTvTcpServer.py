import socket
from SmartTvLogic import SmartTV
from Colors import Colors


class SmartTVServer:
    """TCP Server that allows clients to control a SmartTV instance."""

    BUFFER_SIZE = 128

    def __init__(self, host: str = "127.0.0.1", port: int = 65432, available_channels: int = 120):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.smart_tv = SmartTV(available_channels)

    def start(self):
        """Start the SmartTV server and wait for incoming connections."""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            print(f"Server listening on {self.host}:{self.port}")

            while True:
                conn, addr = self.server_socket.accept()
                print(f"Connection established with {addr}")
                self.handle_client(conn)

        except Exception as e:
            print(Colors.colorize(f"Server error: {e}", False))
        finally:
            self.shutdown()

    def handle_client(self, conn: socket.socket):
        """Handle requests from a single client until it disconnects."""
        try:
            with conn:
                while True:
                    data = conn.recv(self.BUFFER_SIZE)
                    if not data:
                        print("Client disconnected")
                        break

                    command_parts = data.decode(errors="ignore").strip().lower().split()
                    if not command_parts:
                        self.send_response(conn, "Invalid command")
                        continue

                    command = command_parts[0]
                    if command == "turn":
                        self.handle_turn(conn, command_parts)
                    elif command == "status":
                        self.handle_status(conn)
                    elif command == "channel":
                        self.handle_channel(conn, command_parts)
                    elif command == "quit":
                        self.handle_quit(conn)
                        break  # exit client loop, only closes this client
                    else:
                        self.handle_unsupported(conn)

        except Exception as e:
            print(Colors.colorize(f"Error handling client: {e}", False))

    def handle_turn(self, conn: socket.socket, parts: list[str]):
        """Handle 'turn on/off' commands."""
        if len(parts) < 2:
            self.send_response(conn, "Usage: turn <on|off>")
            return

        action = parts[1]
        if action == "on":
            success, msg = self.smart_tv.turnOn()
        elif action == "off":
            success, msg = self.smart_tv.turnOff()
        else:
            self.send_response(conn, "Usage: turn <on|off>")
            return

        self.send_response(conn, Colors.colorize(msg, success))

    def handle_status(self, conn: socket.socket):
        """Report whether the SmartTV is on or off."""
        state = "on" if self.smart_tv.is_on else "off"
        self.send_response(conn, f"Smart TV is {state}")

    def handle_channel(self, conn: socket.socket, parts: list[str]):
        """Handle channel-related commands."""
        if len(parts) < 2:
            self.send_response(conn, "Usage: channel <total|active|set <#int>|down|up>")
            return

        action = parts[1]
        try:
            if action == "total":
                success, msg = self.smart_tv.getNumberOfChannels()
            elif action == "active":
                success, msg = self.smart_tv.getChannel()
            elif action == "set":
                if len(parts) < 3:
                    self.send_response(conn, Colors.colorize("Channel set is missing a value", False))
                    return
                try:
                    new_channel = int(parts[2])
                except ValueError:
                    self.send_response(conn, Colors.colorize("Channel set value must be an integer", False))
                    return
                success, msg = self.smart_tv.setChannel(new_channel)
            elif action == "down":
                success, msg = self.smart_tv.downChannel()
            elif action == "up":
                success, msg = self.smart_tv.upChannel()
            else:
                self.send_response(conn, "Usage: channel <total|active|set <#int>|down|up>")
                return

            self.send_response(conn, Colors.colorize(msg, success))

        except Exception as e:
            error_msg = f"Error in handle_channel: {e}"
            print(Colors.colorize(error_msg, False))
            self.send_response(conn, Colors.colorize(error_msg, False))

    def handle_unsupported(self, conn: socket.socket):
        """Handle unsupported commands."""
        msg = "Unsupported command received"
        print(Colors.colorize(msg, False))
        self.send_response(conn, Colors.colorize(msg, False))

    @staticmethod
    def send_response(conn: socket.socket, message: str):
        """Send a message to the client."""
        conn.sendall((message + "\n").encode())

    def handle_quit(self, conn: socket.socket):
        msg = "Connection closed by client request"
        print(Colors.colorize(msg, False))
        self.send_response(conn, msg)

    def shutdown(self):
        """Shutdown the server socket gracefully."""
        print("Shutting down server...")
        self.server_socket.close()


if __name__ == "__main__":
    server = SmartTVServer()
    server.start()
