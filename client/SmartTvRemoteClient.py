import socket
import threading
import sys

PROMPT = ">> "
print_lock = threading.Lock()  # prevent message overlap from threads


# ------------------- Thread-safe print -------------------
def safe_print(*args, **kwargs):
    """Thread-safe print that repositions the input prompt correctly."""
    with print_lock:
        # Clear the current input line
        sys.stdout.write("\r")
        sys.stdout.flush()
        print(*args, **kwargs)
        # Reprint the prompt cleanly
        sys.stdout.write(PROMPT)
        sys.stdout.flush()


# ------------------- Protocol Selection -------------------
def choose_protocol():
    while True:
        choice = input("Which protocol would you like to use? (1 = TCP, 2 = UDP)\n>> ").strip()
        if choice == "1":
            return socket.SOCK_STREAM
        elif choice == "2":
            return socket.SOCK_DGRAM
        print("Invalid choice. Please enter 1 or 2.")


# ------------------- Listener Threads -------------------
def tcp_listener(sock):
    """Continuously listen for TCP server messages."""
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                safe_print("\n[SERVER] Disconnected.")
                break
            msg = data.decode("utf-8", "ignore").strip()
            if msg:
                safe_print(f"[SERVER] {msg}")
        except Exception:
            break


def udp_listener(sock):
    """Continuously listen for UDP notifications."""
    while True:
        try:
            data, _ = sock.recvfrom(4096)
            msg = data.decode("utf-8", "ignore").strip()
            if msg:
                safe_print(f"[SERVER] {msg}")
        except Exception:
            break


# ------------------- Main Client -------------------
def main():
    protocol = choose_protocol()
    proto_name = "TCP" if protocol == socket.SOCK_STREAM else "UDP"
    print(f"Selected protocol: {proto_name}")

    while True:
        addr_input = input("Enter SmartTV address (e.g. 127.0.0.1:65431) or 'quit' to exit:\n>> ").strip()
        if addr_input.lower() == "quit":
            print("Goodbye.")
            break

        try:
            host, port_str = addr_input.split(":")
            address = (host, int(port_str))
            s = socket.socket(socket.AF_INET, protocol)

            # --- TCP ---
            if protocol == socket.SOCK_STREAM:
                s.connect(address)
                print(f"Connected to {address} via TCP.")
                threading.Thread(target=tcp_listener, args=(s,), daemon=True).start()

            # --- UDP ---
            else:
                s.bind(("", 0))
                local_addr = s.getsockname()
                print(f"UDP client bound to {local_addr}, sending to {address}")
                threading.Thread(target=udp_listener, args=(s,), daemon=True).start()

            # --- Main input loop ---
            while True:
                try:
                    cmd = input(PROMPT).strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nExiting client.")
                    break

                if not cmd:
                    continue
                if cmd.lower() in ("quit", "exit"):
                    safe_print("Closing connection...")
                    if protocol == socket.SOCK_STREAM:
                        try:
                            s.sendall(cmd.encode("utf-8"))
                        except Exception:
                            pass
                    break

                try:
                    if protocol == socket.SOCK_STREAM:
                        s.sendall(cmd.encode("utf-8"))
                    else:
                        s.sendto(cmd.encode("utf-8"), address)
                except Exception as e:
                    safe_print(f"[Error] Failed to send: {e}")
                    break

            s.close()
            safe_print("Connection closed.\n")

        except Exception as e:
            safe_print(f"[Connection error] {e}")
            safe_print("Try entering a new address.\n")


if __name__ == "__main__":
    main()
