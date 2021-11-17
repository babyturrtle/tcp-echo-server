""" TCP Echo Server """

import logging
import threading
import socket
import select

logging.basicConfig(format='%(levelname)s - %(asctime)s - %(message)s', datefmt='%H:%M:%S', level=logging.DEBUG)


class EchoHandler:
    """The request handler class for echo server"""

    def __init__(self, request, srvr) -> None:
        self.request = request
        self.server = srvr
        self.is_finished = False
        self.handle()

    def handle(self) -> None:
        """Implement communication to the client"""
        while True:
            data = self.request.recv(1024)
            cur_thread = threading.current_thread()
            response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
            if data:
                logging.info(f'Echo: {data}')
                self.request.sendall(response)
            else:
                self.finish()

    def finish(self) -> None:
        logging.info(f'Removing: {self.request}')
        self.request.close()
        self.is_finished = True


class EchoServer:
    """Echo server class"""

    address_family: socket.AddressFamily = socket.AF_INET
    socket_type: socket.SocketKind = socket.SOCK_STREAM
    request_queue_size: int = 100

    def __init__(self, server_address: tuple, echo_handler) -> None:
        self.server_address = server_address
        self.echo_handler = echo_handler
        self.socket = socket.socket(self.address_family, self.socket_type)
        self.socket.settimeout(5)
        self.socket.setblocking(False)
        self.inputs = [self.socket]

        try:
            self.server_bind()
            self.server_activate()
        except:
            self.server_close()
            raise

    def server_bind(self) -> None:
        """Binds the server"""

        self.socket.bind(self.server_address)
        logging.info(f'Binding to {self.server_address[0]}:{self.server_address[1]}')

    def server_activate(self) -> None:
        """Activates the server"""

        self.socket.listen(self.request_queue_size)
        logging.info(f'Listening on {self.server_address[0]}:{self.server_address[1]}')

    def server_close(self) -> None:
        """Cleans up the server"""

        self.socket.close()
        logging.info(f'Closing the socket...')

    def serve_forever(self, poll_interval: int = 0.5) -> None:
        """Handle one request at a time until shutdown"""

        while True:
            readable, writable, errored = select.select(self.inputs, [], [], poll_interval)

            for s in readable:
                if s == self.socket:
                    self.handle_request()
                else:
                    self.echo_handler(s, self.socket).handle()
                    if self.echo_handler.is_finished:
                        self.inputs.remove(s)

    def handle_request(self) -> None:
        try:
            request, client_address = self.socket.accept()
            request.setblocking(False)
            self.inputs.append(request)
            logging.info(f'Connection: {client_address}')

        except OSError:
            return


if __name__ == "__main__":

    HOST, PORT = "localhost", 2222

    server = EchoServer((HOST, PORT), EchoHandler)

    host, port = server.server_address
    server_thread = threading.Thread(target=server.serve_forever())
    server_thread.daemon = True
    server_thread.start()
