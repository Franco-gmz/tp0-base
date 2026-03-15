def client_template(i):

    return f"""  client{i}:
    container_name: client{i}
    image: client:latest
    volumes:
      - ./client/config.yaml:/config.yaml
    entrypoint: /client
    environment:
      - CLI_ID={i}
      - CLI_LOG_LEVEL=DEBUG
    networks:
      - testing_net
    depends_on:
      - server

"""

def write_clients(file, cantidad):

    for i in range(1, cantidad + 1):
        file.write(client_template(i))