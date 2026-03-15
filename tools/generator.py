import sys

from common_writer import write_header
from server_writer import write_server
from clients_writer import write_clients
from networks_writer import write_networks


def main():

    if len(sys.argv) != 3:
        print("Uso: generator.py <archivo_salida> <cantidad_clientes>")
        sys.exit(1)

    output_file = sys.argv[1]
    clients = int(sys.argv[2])

    with open(output_file, "w") as file:

        write_header(file)
        write_server(file)
        write_clients(file, clients)
        write_networks(file)


if __name__ == "__main__":
    main()