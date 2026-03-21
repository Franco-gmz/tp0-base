import configparser
import logging
import os
import sys

from common.client import Client, ClientConfig


def parse_period(period_str):
    if period_str.endswith("ms"):
        return int(period_str[:-2]) / 1000
    return float(period_str)


def init_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-5s    %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def main():
    init_logger()

    config = configparser.ConfigParser()
    config.read("/config.ini")

    server_address = config["server"]["address"]
    iterations = int(config["loop"]["amount"])
    period = parse_period(config["loop"]["period"])
    cli_id = os.getenv("CLI_ID", "1")

    client_config = ClientConfig(
        client_id=cli_id,
        server_address=server_address,
        loop_amount=iterations,
        loop_period=period,
    )

    client = Client(client_config)
    client.start_client_loop()


if __name__ == "__main__":
    main()