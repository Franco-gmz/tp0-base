def networks_template():
    return """
networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
"""

def write_networks(file):
    file.write(networks_template())