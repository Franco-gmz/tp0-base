def server_template(clients):
    return f"""  server:
    container_name: server
    image: server:latest
    volumes:
      - ./server/config.ini:/server/config.ini
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - CLIENTS={clients}
    networks:
      - testing_net
"""

def write_server(file, clients):
    file.write(server_template(int(clients)))