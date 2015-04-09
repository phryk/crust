# -*- coding: utf-8 -*-

from pickle import Pickler, Unpickler
from .ipc import IPCServer
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

    debug = None
    environment = None
    running = None
    command_list = None
    ipc_server = None

    
    def __init__(self, debug=False):

        self.running = False
        self.debug = debug
        self.environment = Environment

        self.command_list = {
            '': EmptyCommand,
            'exit': ExitCommand,
            'test': TestCommand
        }

        self.ipc_server = IPCServer('/tmp/crust', listener=self)



    def __call__(self, command_line):

        try:

            command = self.read_command(command_line)
            return command()

        except Crustception:

            return "ERROR: Shit happened."


    
    def start(self):

        self.running = True
        self.ipc_server.start()



    def read_command(self, command_line):

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
    
