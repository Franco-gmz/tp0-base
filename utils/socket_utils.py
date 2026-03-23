def recv_exact(sock, n):
        data = b""
        while len(data) < n:
            chunk = sock.recv(n - len(data))

            if not chunk:
                raise ConnectionError("Socket connection broken")

            data += chunk

        return data