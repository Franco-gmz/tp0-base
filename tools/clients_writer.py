def client_template(i):

    return f"""  client{i}:
    container_name: client{i}
    image: client:latest
    volumes:
      - ./client/config.ini:/config.ini
    entrypoint: python3 /main.py
    environment:
      - CLI_ID={i}
      - NOMBRE=NOMBRE{i}
      - APELLIDO=APELLIDO{i}
      - DOCUMENTO={i}{i}{i}{i}{i}{i}{i}{i}
      - NACIMIENTO=1998-01-04
      - NUMERO={i}
    networks:
      - testing_net
    depends_on:
      - server

"""

def write_clients(file, cantidad):

    for i in range(1, cantidad + 1):
        file.write(client_template(i))