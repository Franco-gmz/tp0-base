def recv_exact(sock, n):
        data = b""

        while len(data) < n:
            chunk = sock.recv(n - len(data))

            if not chunk:
                raise RuntimeError("Socket connection broken")

            data += chunk

        return data