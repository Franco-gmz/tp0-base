FROM python:3.9.7-slim

COPY server /
COPY protocol /protocol
COPY domain /domain
COPY utils /utils

WORKDIR /

RUN python -m unittest tests/test_common.py
ENTRYPOINT ["/bin/sh"]
