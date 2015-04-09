# -*- coding: utf-8 -*-

from socket import socket, AF_UNIX, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, SHUT_RDWR
from socket import error as socketError
from os import unlink, path
from pickle import Pickler, Unpickler
from .error import * # TODO: assess how much, if any, risk 'import *' poses.
from .enforcers import *

class Environment(object):

    handle = None
    loader = None
    writer = None
    data = None


    def __init__(self):
    
        self.handle = open("environment.pickle", 'w+')
        self.loader = Unpickler(self.handle)
        self.writer = Pickler(self.handle)

        try:
            self.data = self.loader.load()
        except EOFError:
            print "WARNING: Empty environment, creating environment file."
            self.data = {}
            self.write(self.data)


    def write(self, data):

        self.writer.dump(data)



class Daemon(object):

    addr = None
    command_list = None
    connected = None
    debug = None
    environment = None
    max_command_size = None

    
    def __init__(self, addr, max_command_size=4096, debug=False):

        try:
            unlink(addr)
        except OSError:
            if path.exists(addr):
                raise

        self.addr = addr
        self.connected = False
        self.max_command_size = max_command_size
        self.debug = debug
        self.environment = Environment()

        self.command_list = {
            '': EmptyCommand,
            'exit': ExitCommand,
            'test': TestCommand
        }

        sock = socket(AF_UNIX, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind(addr)
        sock.listen(0)

        self.sock = sock


    def start(self):

        self.running = True
        self.loop()


    def loop(self):

        while self.running:

            connected = True
            (conn, addr) = self.sock.accept()
            
            while connected:

                # Get new command line from file socket
                command_line = conn.recv(self.max_command_size).decode('utf-8')

                try:
                    command = self.parse_command(command_line)

                except CommandValidationError as e:

                    conn.send("ERROR: Command validation failed.")

                    if self.debug == True:
                        print "Non-fatal exception for command validation."
                        print e

                    continue # restart loop of this connection

                try:
                    return_message = command()

                except CommandExecutionError as e:
                    conn.send("ERROR: Command execution failed.")

                    if self.debug is True:
                        print "Exception for command execution."
                        print e


                try:
                    conn.send(return_message)

                except socketError as e:
                    #print "Mystery Exception: ", e.__class__, dir(e)
                    conn.shutdown(SHUT_RDWR)
                    conn.close()
                    connected = False


    def parse_command(self, command_line):

        print "Daemon read triggered."

        line_segments = command_line.split(' ')
        command_key = line_segments[0]

        if not command_key in self.command_list.keys():
            raise CommandValidationError("Unknown command key '%s' used, known are: %s" % (command_key, ', '.join(self.command_list.keys())))
        
        command = self.command_list[command_key](self.environment)

        count_passed = len(line_segments) - 1
        count_expected = len(command.parameter_list)

        if count_passed != count_expected:
            raise CommandValidationError("Incorrect parameter count for command '%s'. Expected %d, got %d." % (command.__class__.__name__, count_expected, count_passed))

        for idx, value in enumerate(command.parameters):

            value = line_segments[idx+1]
            command.bind_param(idx, value)

        return command


    def kill(self):

        self.running = False


class Command(object):

    # Base command class.

    environment = None
    parameter_list = [] # Used to whitelist parameters and set data hygiene enforcement callbacks


    def __init__(self, environment):

        # Initialize self.parameters with 'None' for each whitelisted parameter.
        self.parameters = []
        for idx, enforcer in enumerate(self.parameter_list):
            #self.parameters[idx] = None
            self.parameters.append(None)


    def __call__(self):

        for idx, value in enumerate(self.parameters):
            if value is None:
                raise CommandExecutionError("Missing parameter %d for command '%s'." % (idx, self.__class__.__name__))

        return self.execute()


    def bind_param(self, idx, value):

        if idx > (len(self.parameters) - 1):
            raise CommandValidationError("Tried to bind unkown parameter %d to command '%s'." % (idx, self.__class__.__name__))
        else:
            self.parameters[idx] = self.parameter_list[idx](value) # raises CommandValidationError on failure.


    def execute(self):

        raise NotImplementedError("%s.execute() not implemented." % (self.__class__.__name__,))



class EmptyCommand(Command):

    def execute(self):
        return ""



class ExitCommand(Command):

    def execute(self):
        return "Bye."


class TestCommand(Command):

    parameter_list = [
        enforce_integer
    ]

    def execute(self):
        return str(self.parameters[0])
    
