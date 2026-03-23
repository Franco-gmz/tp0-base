def client_template(i):

    return f"""  client{i}:
    container_name: client{i}
    image: client:latest
    volumes:
      - ./client/config.ini:/config.ini
      - ./.data/agency-{i}.csv:/agency-{i}.csv
    entrypoint: python3 /main.py
    environment:
      - CLI_ID={i}
      - BATCH_FILE=./agency-{i}.csv
    networks:
      - testing_net
    depends_on:
      - server

"""

def write_clients(file, cantidad):

    for i in range(1, cantidad + 1):
        file.write(client_template(i))