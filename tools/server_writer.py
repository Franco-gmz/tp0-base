def server_template():
    return """  server:
    container_name: server
    image: server:latest
    volumes:
      - ./server/config.ini:/server/config.ini
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - testing_net
"""

def write_server(file):
    file.write(server_template())