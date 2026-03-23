import sys
import os
import zipfile

from common_writer import write_header
from server_writer import write_server
from clients_writer import write_clients
from networks_writer import write_networks


def ensure_datasets():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, ".data")
    zip_path = os.path.join(data_dir, "dataset.zip")

    expected_file = os.path.join(data_dir, "agency-1.csv")

    if os.path.exists(expected_file):
        return

    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"No se encontró {zip_path}")

    print("Descomprimiendo datasets...")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(data_dir)


def main():
    if len(sys.argv) != 3:
        print("Uso: generator.py <archivo_salida> <cantidad_clientes>")
        sys.exit(1)

    ensure_datasets()

    output_file = sys.argv[1]
    clients = int(sys.argv[2])

    with open(output_file, "w") as file:
        write_header(file)
        write_server(file)
        write_clients(file, clients)
        write_networks(file)


if __name__ == "__main__":
    main()