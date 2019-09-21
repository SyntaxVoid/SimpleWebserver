import socket

def start_server(host, port):
  """ Starts a simple server that sends a welcome message for every request """
  listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  listener.bind((host, port))
  listener.listen(1)
  print(f"Serving HTTP on port {port}. . .")
  while True:
    client_connection, _ = listener.accept()
    request = client_connection.recv(1024)
    decoded = request.decode("UTF-8")

    print(decoded)
    response = b"""\
HTTP/1.1 200 OK

Welcome to the shark server. . .
"""
    client_connection.sendall(response)
    client_connection.close()
  return

if __name__ == "__main__":
  host, port = ("localhost", 8080)
  start_server(host, port)
  