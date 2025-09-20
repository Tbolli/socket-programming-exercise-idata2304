import socket

def choose_protocol():
    while True:
        choice = input("Which protocol would you like to use (write either 1 or 2):\n1. TCP\n2. UDP\n>> ").strip()
        if choice == "1":
            return socket.SOCK_STREAM
        elif choice == "2":
            return socket.SOCK_DGRAM
        else:
            print("Invalid choice: please enter 1 for TCP or 2 for UDP")

def get_address():
    while True:
        try:
            host_str, port_str = input("Enter SmartTV address <127.0.0.1:65432> or type 'quit' to exit:\n>> ").strip().split(":")
            return host_str, int(port_str)
        except ValueError:
            print("Invalid format. Use <IP:PORT>.")

def main():
    protocol = choose_protocol()
    print(f"Selected protocol: {'TCP' if protocol == socket.SOCK_STREAM else 'UDP'}")

    while True:
        addr_input = input("Enter SmartTV address <127.0.0.1:65432> or type 'quit' to exit:\n>> ").strip()
        if addr_input.lower() == 'quit':
            print("Exiting client.")
            break

        try:
            host_str, port_str = addr_input.split(":")
            address = (host_str, int(port_str))

            with socket.socket(socket.AF_INET, protocol) as s:
                if protocol == socket.SOCK_STREAM:
                    s.connect(address)
                print(f"Connected to {address}")

                while True:
                    user_input = input(">> ").strip()
                    if user_input.lower() in ("quit", "exit"):
                        print("Closing connection.")
                        break

                    s.sendall(user_input.encode())
                    response = s.recv(128).decode(errors="ignore")
                    print(response)

        except Exception as e:
            print(f"Connection failed or lost: {e}")
            print("You can try a new address.")

if __name__ == "__main__":
    main()