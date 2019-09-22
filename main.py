# John Gresl -- J.GRESL12@GMAIL.COM

import datetime
from importlib import import_module
import io
import socket
import sys


class WSGIServer(object):
  """
  Implements a very basic Web Server Gateway Interface that handles one
  connection at a time.
  """
  address_family     = socket.AF_INET
  socket_type        = socket.SOCK_STREAM
  request_queue_size = 1

  def __init__(self, host, port, app):
    """
    Initializes the server's arguments and creates the listener socket.
    Does not do any handling of requests. It is your responsibility to call
    serve_forever on the WSGIServer object you create.

    Inputs:
      host: str - The hostname (usually an empty string or 'localhost')
      port: int - The port number to run off of
      app:  callable - A callable object from a framework like Flask or Django
    """
    self.listener = socket.socket(self.address_family, self.socket_type)
    self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.listener.bind((host, port))
    self.listener.listen(self.request_queue_size)
    self.server_name = socket.getfqdn(host)
    self.server_host = host
    self.server_port = port
    self.headers = []
    self.app = app
    return
  
  @staticmethod
  def _curl(msg, prefix = ""):
    """ 
    Given a msg (usually a request or a response), simulates output in the
    format of a curl command like on unix. Prefix can be ommitted but should
    be ">" for an outgoing request and "<" for an incoming response.
    Personally, I think curl implements this backwards... but that's none of
    my business...

    Inputs:
      msg: str - The message body
      prefix: str - The character to put before each line in msg.
        Blank by default. You should use > and < for outgoing and incoming msgs
    """
    print("".join(f"{prefix} {line}\n" for line in msg.splitlines()))
    return

  def serve_forever(self):
    """ 
    Servers forever by accepting all connections and then handling requests
    one at a time. If an exception occurs while handling a request, the 
    exception is displayed. This could potentially be a problem if an
    exception occurs during data transmission to the client. Further data
    sent may be corrupted! The client's connection is closed to mitigate this.
    """
    print(f"Now serving HTTP at {self.server_port}. . .")
    while True:
      self.client_con, self.client_addr = self.listener.accept()
      self.request = self.client_con.recv(1024).decode("UTF-8")
      try:
        self.handle_request()
      except Exception as e:
        print("*=*=*=*= Unexpected Error when handling request... *=*=*=*=")
        print(str(e))
        self.client_con.close()
    return
  
  def handle_request(self):
    """
    Handles a single request. If the request is empty, a small message is
    displayed, and no data is transmitted back to the client. This feature
    had to be added since other servers running on my machine kept sending
    empty requests to this one about once a minute... IDK WHY???
    """
    if not self.request:
      print("*=*=*=*= Received Empty Request *=*=*=*=")
      print(f"Client address: {self.client_addr}")
      return
    print("="*78)
    print("Incoming Transmission...")
    self._curl(msg = self.request, prefix = "<")
    request_head = self.request.splitlines()[0].rstrip("\r\n").split()
    self.request_method  = request_head[0]
    self.request_path    = request_head[1]
    self.request_version = request_head[2]
    self.env = self.get_environ()
    unfinished_response = self.app(self.env, self.start_response)
    self.finish_response(unfinished_response)
    return
  
  def get_environ(self):
    """ 
    Returns the standard environment. References for how to make this can be
    found under PEP 333: https://www.python.org/dev/peps/pep-0333/#id19
    """
    return {"wsgi.version":      (1, 0),
            "wsgi.url_scheme":   "http",
            "wsgi.input":        io.StringIO(self.request),
            "wsgi.errors":       sys.stderr,
            "wsgi.multithread":  False,
            "wsgi.multiprocess": False,
            "wsgi.run_once":     False,
            "REQUEST_METHOD":    self.request_method,
            "PATH_INFO":         self.request_path,
            "SERVER_NAME":       self.server_name,
            "SERVER_PORT":       str(self.server_port)}

  def start_response(self, status, response_headers, exc_info = None):
    """ 
    UsElEsS fUnCtIoN. JK. It may not have a purpose but it is part of
    the WSGI specifications so... I guess here it is. 
    """
    if exc_info is not None:
      try:    # We may want to handle the exception later...  But first I have
        pass  # to figure out what will be passed here...?
      finally:
        exc_info = None   # Re-set to None to avoid circular references!
    now = datetime.datetime.now()
    now_str = now.strftime("%a, %d %B %y %H:%M:%S PST")
    version = ".".join(str(i) for i in self.env["wsgi.version"])
    server_headers = [("Date", now_str),
                      ("Server", f"WSGI Server {version}")]
    self.headers = [status, response_headers + server_headers]
    return # This should return a write callable but I'm big dumb rn... :/

  def finish_response(self, result):
    """
    Finishes the response started by self.start_response. The response is sent
    to the client and the connection is closed regardless of a successful
    completion.
    
      Inputs:
        result: Comes from the web framework itself (flask, django, etc)
    """
    try:
      status, response_headers = self.headers
      response = f"HTTP/1.1 {status}\r\n"
      for header in response_headers:
        response += "{}: {}\r\n".format(*header)
      response += "\r\n"
      for data in result:
        response += data.decode("UTF-8")
      print("\nOutgoing Transmission...")
      self._curl(msg = response, prefix = ">")
      self.client_con.sendall(response.encode())
    finally:
      self.client_con.close()
    return
  
if __name__ == "__main__":
  host, port = ("", 8080)
  if len(sys.argv) < 2:
    # sys.exit("Provide a WSGI application object as module:callable")
    app_path = "flask_app:app"
  else:
    app_path = sys.argv[1]
  module_str, app = app_path.split(":")
  module = import_module(module_str)
  app = getattr(module, app)
  httpd = WSGIServer(host, port, app)
  httpd.serve_forever()
