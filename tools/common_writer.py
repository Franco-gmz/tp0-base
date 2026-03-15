def header_template():
    return """name: tp0
services:
"""

def write_header(file):
    file.write(header_template())