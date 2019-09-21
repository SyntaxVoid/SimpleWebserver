# John Gresl -- J.GRESL12@GMAIL.COM

import io
import socket
import sys


class WGSIServer(object):
  """
  Implements a very basic *W*eb *S*erver *G*ateway *I*nterface
  """
  address_family = socket.AF_INET
  socket_type = socket.SOCK_STREAM
  request_queue_size = 1
  
  def __init__(self, addr):
    self.listener = socket.socket(self.address_family, self.socket_type)
    self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.listener.bind(addr)
    self.listener.listen(self.request_queue_size)
    host, port = self.listener.getsockname()[:2]
    self.server_name = socket.getfqdn(host)
    self.server_port = port
    self.headers_set = []
    return

  def set_app(self, app):
    self.app = app
    return

  def serve_forever(self):
    while True:
      self.client_connection, self.client_address = self.listener.accept()
      self.handle_one_request()
    return
  
  def handle_one_request(self):
    self.request = self.client_connection.recv(1024).decode("UTF-8")
    print("".join(f"< {line}\n" for line in self.request.splitlines()))
    self.parse_request()
    env = self.get_environ()
    result = self.app(env, self.start_response)
    self.finish_response(result)
    return
  
  def parse_request(self):
    request_head = self.request.splitlines()[0].rstrip("\r\n")
    self.request_method, self.path, self.request_v = request_head.split()
    return

  def get_environ(self):
    env = {"wsgi.version": (1,0),
           "wsgi.url_scheme": "http",
           "wsgi.input": io.StringIO(self.request),
           "wsgi.errors": sys.stderr,
           "wsgi.multithread": False,
           "wsgi.multiprocess": False,
           "wsgi.run_once": False,
           "REQUEST_METHOD": self.request_method,
           "PATH_INFO": self.path,
           "SERVER_NAME": self.server_name,
           "SERVER_PORT": str(self.server_port)}
    return env

  def start_response(self, status, response_headers, exc_info=None):
    server_headers = [("Date", "Fri, 20 Aug 2019 6:26:40 GMT"),
                      ("Server", "WGSI Server 1.0")]
    
    self.headers_set = [status, response_headers + server_headers]
    return
  
  def finish_response(self, result):
    try:
      status, response_headers = self.headers_set
      response = f"HTTP/1.1 {status}\r\n"
      for header in response_headers:
        response += "{}: {}\r\n".format(*header)
      response += "\r\n"
      for data in result:
        response += data.decode("UTF-8")
      print("".join(f"> {line}\n" for line in response.splitlines()))
      response_bytes = response.encode()
      self.client_connection.sendall(response_bytes)
    finally:
      self.client_connection.close()


def make_server(server_address, app):
  """ Starts a simple server that sends a welcome message for every request """
  server = WGSIServer(server_address)
  server.set_app(app)
  return server

if __name__ == "__main__":
  host, port = ("", 8080)
  if len(sys.argv) < 2:
    # sys.exit("Provide a WSGI application object as a module:callable")
    app_path = "flask_app:app"
  else:
    app_path = sys.argv[1]
  module, app = app_path.split(":")
  module = __import__(module)
  app = getattr(module, app)
  httpd = make_server((host, port), app)
  httpd.serve_forever()
  