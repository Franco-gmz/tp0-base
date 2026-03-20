#!/bin/bash

MESSAGE="hola"
PORT=12345
NETWORK="tp0_testing_net"

RESPONSE=$(docker run --rm --network $NETWORK alpine sh -c "echo $MESSAGE | nc server $PORT" 2>/dev/null)

if [ "$RESPONSE" = "$MESSAGE" ]; then
  echo "action: test_echo_server | result: success"
else
  echo "action: test_echo_server | result: fail"
fi