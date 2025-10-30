import threading
import queue
import traceback
from SmartTvLogic import SmartTV
from helpers.ProtocolConfig import Protocol
from helpers.Colors import Colors
from transport.BaseTransport import BaseTransport
from transport.TcpTransport import TcpTransport
from transport.UdpTransport import UdpTransport


# ------------------- TCP CLIENT HANDLER -------------------
class ClientSession:
    """Handles a single TCP client connection asynchronously."""

    def __init__(self, server, conn, addr):
        self.server = server
        self.conn = conn
        self.addr = addr
        self.queue = queue.Queue()
        self.active = True

        threading.Thread(target=self._recv_loop, name=f"recv-{addr}", daemon=True).start()
        threading.Thread(target=self._send_loop, name=f"send-{addr}", daemon=True).start()

    def send(self, msg: str):
        if not msg.endswith("\n"):
            msg += "\n"
        if self.active:
            self.queue.put(msg)

    def close(self):
        self.active = False
        try:
            self.queue.put_nowait(None)
        except Exception:
            pass
        try:
            self.conn.close()
        except Exception:
            pass

    def _send_loop(self):
        """Continuously send queued messages to this TCP client."""
        while self.active:
            try:
                msg = self.queue.get(timeout=1)
                if msg is None:
                    break
                self.conn.send(msg)
            except queue.Empty:
                continue
            except Exception as e:
                print(Colors.colorize(f"[TCP send error] {self.addr}: {e}", False))
                break
        self.server._remove_client(self)

    def _recv_loop(self):
        """Receive and process commands from the TCP client."""
        try:
            while self.active:
                try:
                    data = self.conn.recv(self.server.BUFFER_SIZE)
                except Exception as e:
                    print(Colors.colorize(f"[TCP recv error] {self.addr}: {e}", False))
                    break
                if not data:
                    break

                for line in data.decode(errors="ignore").splitlines():
                    cmd = line.strip().lower()
                    if cmd:
                        self.server._process_command(self, cmd)
        finally:
            self.server._remove_client(self)


# ------------------- SMART TV SERVER -------------------
class SmartTVServer:
    """Smart TV server supporting:
    - Multiple concurrent TCP clients (each remote runs in its own threads)
    - Connectionless UDP clients
    - Broadcast notifications across all connected clients
    """

    BUFFER_SIZE = 4096

    def __init__(self, transport: BaseTransport, available_channels: int):
        self.smart_tv = SmartTV(available_channels)
        self.transport = transport

        # TCP clients
        self.tcp_clients = set()
        self.tcp_lock = threading.RLock()

        # UDP client addresses (connectionless)
        self.udp_clients = set()
        self.udp_lock = threading.RLock()

        # Command dispatch map
        self.dispatch = {
            Protocol.COMMANDS["TURN_ON"]: self._turn_on,
            Protocol.COMMANDS["TURN_OFF"]: self._turn_off,
            Protocol.COMMANDS["STATUS"]: self._status,
            Protocol.COMMANDS["CHANNEL_TOTAL"]: self._channel_total,
            Protocol.COMMANDS["CHANNEL_ACTIVE"]: self._channel_active,
            Protocol.COMMANDS["CHANNEL_SET"]: self._channel_set,
            Protocol.COMMANDS["CHANNEL_DOWN"]: self._channel_down,
            Protocol.COMMANDS["CHANNEL_UP"]: self._channel_up,
            Protocol.COMMANDS["QUIT"]: self._quit,
        }

    # ------------------- TRANSPORT ENTRYPOINT -------------------

    def handle_client(self, conn):
        """Called by the transport for each new TCP connection or UDP datagram."""
        if hasattr(conn, "server_socket"):  # UDP (connectionless)
            self._handle_udp_datagram(conn)
        else:  # TCP (stateful)
            addr = getattr(conn, "addr", "unknown")
            client = ClientSession(self, conn, addr)
            with self.tcp_lock:
                self.tcp_clients.add(client)
            print(f"[TCP] Client connected: {addr}")

    # ------------------- UDP HANDLING -------------------

    def _handle_udp_datagram(self, conn):
        """Handle one UDP request (connectionless)."""
        try:
            data = conn.recv(self.BUFFER_SIZE)
        except Exception as e:
            print(Colors.colorize(f"[UDP recv error] {e}", False))
            return

        if not data:
            return

        addr = getattr(conn, "addr", None)
        if addr:
            with self.udp_lock:
                self.udp_clients.add(addr)

        try:
            text = data.decode("utf-8", "ignore").strip().lower()
        except Exception:
            text = str(data).strip().lower()

        if text:
            self._process_command(conn, text)

    # ------------------- CORE SENDING -------------------

    def _send_to(self, target, message: str):
        """Send to either a TCP session or UDP client."""
        if not message.endswith("\n"):
            message += "\n"

        if isinstance(target, ClientSession):  # TCP
            target.send(message)

        elif hasattr(target, "send") and hasattr(target, "addr"):  # UDP conn wrapper
            try:
                target.send(message)
            except Exception as e:
                print(Colors.colorize(f"[UDP send error] {e}", False))

        elif isinstance(target, tuple) and len(target) == 2:  # UDP addr tuple
            sock = getattr(self.transport, "server_socket", None)
            if sock:
                try:
                    sock.sendto(message.encode("utf-8"), target)
                except Exception as e:
                    print(Colors.colorize(f"[UDP sendto error] {e}", False))

    # ------------------- BROADCAST -------------------

    def broadcast(self, message: str, exclude=None):
        """Send a message to all connected TCP and UDP clients."""
        if not message.endswith("\n"):
            message += "\n"

        # TCP clients
        with self.tcp_lock:
            for client in list(self.tcp_clients):
                if client is not exclude:
                    client.send(message)

        # UDP clients
        sock = getattr(self.transport, "server_socket", None)
        if not sock:
            return
        with self.udp_lock:
            for addr in list(self.udp_clients):
                if hasattr(exclude, "addr") and addr == exclude.addr:
                    continue
                try:
                    sock.sendto(message.encode("utf-8"), addr)
                except Exception as e:
                    print(Colors.colorize(f"[UDP broadcast error] {e}", False))

    # ------------------- CLIENT MANAGEMENT -------------------

    def _remove_client(self, client):
        with self.tcp_lock:
            if client in self.tcp_clients:
                self.tcp_clients.remove(client)
        client.close()
        print(f"[TCP] Client {client.addr} disconnected")

    # ------------------- COMMAND DISPATCH -------------------

    def _process_command(self, client, text: str):
        if not text:
            self._send_to(client, "Invalid command")
            return

        parts = text.split()
        for length in range(len(parts), 0, -1):
            cmd = " ".join(parts[:length])
            handler = self.dispatch.get(cmd)
            if handler:
                try:
                    quit_flag = handler(client, parts[length:])
                    if quit_flag and isinstance(client, ClientSession):
                        client.close()
                    return
                except Exception:
                    traceback.print_exc()
                    self._send_to(client, Colors.colorize("Internal server error", False))
                    return
        self._unsupported(client)

    # ------------------- COMMAND HANDLERS -------------------

    def _turn_on(self, client, _):
        ok, msg = self.smart_tv.turnOn()
        self._send_to(client, Colors.colorize(msg, ok))

    def _turn_off(self, client, _):
        ok, msg = self.smart_tv.turnOff()
        self._send_to(client, Colors.colorize(msg, ok))

    def _status(self, client, _):
        state = "on" if self.smart_tv.is_on else "off"
        self._send_to(client, f"Smart TV is {state}")

    def _channel_total(self, client, _):
        ok, msg = self.smart_tv.getNumberOfChannels()
        self._send_to(client, Colors.colorize(msg, ok))

    def _channel_active(self, client, _):
        ok, msg = self.smart_tv.getChannel()
        self._send_to(client, Colors.colorize(msg, ok))

    def _channel_set(self, client, args):
        if not args:
            self._send_to(client, f"Usage: {Protocol.COMMANDS['CHANNEL_SET']} <#int>")
            return
        try:
            new_ch = int(args[0])
        except ValueError:
            self._send_to(client, Colors.colorize("Channel must be an integer", False))
            return

        ok, msg = self.smart_tv.setChannel(new_ch)
        self._send_to(client, Colors.colorize(msg, ok))
        if ok:
            self.broadcast(f"[Notification] Channel changed to {new_ch}", exclude=client)

    def _channel_down(self, client, _):
        ok, msg = self.smart_tv.downChannel()
        self._send_to(client, Colors.colorize(msg, ok))
        if ok:
            _, ch = self.smart_tv.getChannel()
            self.broadcast(f"[Notification] Channel changed to {ch}", exclude=client)

    def _channel_up(self, client, _):
        ok, msg = self.smart_tv.upChannel()
        self._send_to(client, Colors.colorize(msg, ok))
        if ok:
            _, ch = self.smart_tv.getChannel()
            self.broadcast(f"[Notification] Channel changed to {ch}", exclude=client)

    def _quit(self, client, _):
        self._send_to(client, "Goodbye!")
        print(f"[QUIT] {getattr(client, 'addr', 'unknown')}")
        return True

    def _unsupported(self, client):
        msg = "Unsupported command received"
        print(Colors.colorize(msg, False))
        self._send_to(client, Colors.colorize(msg, False))

    # ------------------- SERVER LIFECYCLE -------------------

    def start(self):
        self.transport.start()

    def shutdown(self):
        print("Server shutting down...")
        with self.tcp_lock:
            for c in list(self.tcp_clients):
                c.close()
        with self.udp_lock:
            self.udp_clients.clear()
        if hasattr(self.transport, "shutdown"):
            try:
                self.transport.shutdown()
            except Exception:
                pass


# ------------------- ENTRY POINT -------------------
if __name__ == "__main__":
    host, port = "127.0.0.1", 65431
    # Choose one
    # transport = UdpTransport(host, port, None)
    transport = TcpTransport(host, port, None)

    server = SmartTVServer(transport, available_channels=120)
    transport.server = server
    server.start()
