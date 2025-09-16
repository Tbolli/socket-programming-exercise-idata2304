import socket


class SmartTVServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 65432, available_channels: int = 120):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_on = False
        self.available_channels = available_channels
        self.active_channel = 1

    def start(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            print(f"Server listening on {self.host}:{self.port}")

            while True:
                # Waiting for a client
                conn, addr = self.server_socket.accept()
                print(f"Connection established with {addr}")
                # Handle this client exclusively
                self.handle_client(conn)

        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.shutdown()

    def handle_client(self, conn: socket.socket):
        try:
            with conn:
                while True:
                    data = conn.recv(128)
                    if not data:  # Client closed connection
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
                    elif command == "channle":
                        self.handle_channel(conn, command_parts)
                    else:
                        self.handle_unsupported(conn)

        except Exception as e:
            print(f"Error handling client: {e}")

    def handle_turn(self, conn: socket.socket, command_parts: list):
        if len(command_parts) < 2:
            self.send_response(conn, "Usage: turn <on|off>")
            return

        action = command_parts[1]
        if action == "on":
            if self.is_on:
                self.send_response(conn, "Smart TV is already turned on")
            else:
                self.is_on = True
                self.send_response(conn, "Smart TV is turned on")

        elif action == "off":
            if not self.is_on:
                self.send_response(conn, "Smart TV is already turned off")
            else:
                self.is_on = False
                self.send_response(conn, "Smart TV is turned off")
        else:
            self.send_response(conn, "Usage: turn <on|off>")

    def handle_status(self, conn: socket.socket):
        self.send_response(conn, f"Smart TV is {"on" if self.is_on else "off"}")

    def handle_channel(self, conn: socket.socket, command_parts: list):
        if not self.is_on:
            self.send_response(conn, "Smart TV is off | Unable to do anything with the active channel")
            return

        if len(command_parts) < 2:
            self.send_response(conn, "Usage: channel <total|active|set <#int>|down|up>")
            return

        action = command_parts[1]

        try:
            if action == "total":
                self.send_response(conn, f"Total number of channels: {self.available_channels}")

            elif action == "active":
                self.send_response(conn, f"Active channel: {self.active_channel}")

            elif action == "set":
                if len(command_parts) < 3:
                    self.send_response(conn, "Channel set is missing a value")
                    return

                try:
                    new_channel = int(command_parts[2])
                except ValueError:
                    self.send_response(conn, "Channel set value must be an integer")
                    return

                if new_channel < 1 or new_channel > self.available_channels:
                    self.send_response(conn, f"Channel {new_channel} is out of range, valid range: 1-{self.available_channels}")
                    return

                self.active_channel = new_channel
                self.send_response(conn, f"Active channel set to: {self.active_channel}")

            elif action == "down":
                if self.active_channel == 1:
                    self.send_response(conn, "Channel cannot go any lower than channel 1")
                    return
                self.active_channel -= 1
                self.send_response(conn, f"Channel went down to {self.active_channel}")

            elif action == "up":
                if self.active_channel == self.available_channels:
                    self.send_response(conn, f"Channel cannot go any higher than channel {self.available_channels}")
                    return
                self.active_channel += 1
                self.send_response(conn, f"Channel went up to {self.active_channel}")

            else:
                self.send_response(conn, "Usage: channel <total|active|set <#int>|down|up>")

        except Exception as e:
            print(f"Error in handle_channel: {e}")
            self.send_response(conn, f"Error: {e}")

    def handle_unsupported(self, conn: socket.socket):
        print("Unsupported command received")
        self.send_response(conn, "Unsupported command")

    @staticmethod
    def send_response(conn: socket.socket, message: str):
        conn.sendall((message + "\n").encode())

    def shutdown(self):
        print("Shutting down server...")
        self.server_socket.close()


if __name__ == "__main__":
    server = SmartTVServer()
    server.start()