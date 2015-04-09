# -*- coding: utf-8 -*-

from socket import socket, AF_UNIX, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, SHUT_RDWR
from socket import error as socketError
from threading import Thread
from os import unlink, path

class IPCServer(Thread):

    daemon = True
    addr = None
    die = None
    listener = None
    sock = None
    max_command_size = None

    def __init__(self, addr, listener, max_command_size = 4096):

        try:
            unlink(addr)
        except OSError:
            if path.exists(addr):
                raise

        sock = socket(AF_UNIX, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind(addr)
        sock.listen(0)

        self.sock = sock
        self.max_command_size = max_command_size
        self.die = False
        self.addr = addr
        self.listener = listener

        super(IPCServer, self).__init__()


    def run(self):
        print "IPCServer.run" 
        while not self.die:
            self.handle_client()

        print "self.die:", self.die


    def kill(self):
        self.die = True


    def handle_client(self):

        connected = True
        (conn, addr) = self.sock.accept()

        print "client: ", dir(conn)

        print "IPCServer.handle_client entering loop."
        while connected:

            raw_command = conn.recv(self.max_command_size).decode('utf-8')
            print raw_command
            val = self.listener(raw_command)
            print "command return val: ", val

            try:
                conn.send(val)

            except socketError as e:
                #print "Mystery Exception: ", e.__class__, dir(e)
                conn.shutdown(SHUT_RDWR)
                conn.close()
                connected = False


class IPCClient(object):

    sock = None
    addr = None


    def __init__(self, addr):

        sock = socket(AF_UNIX, SOCK_STREAM)
        sock.connect(addr)
        sock.send("oink\nwtf☠")
        print "oink?"
        while True:
            pass
