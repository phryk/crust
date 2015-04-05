#!/usr/bin/env python

from sys import exit, stdin
from pickle import Pickler, Unpickler
from error import *
from enforcers import enforce_integer



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


class Shell(object):

    debug = None
    environment = None
    running = None
    command_list = None


    def __init__(self, debug=False):

        self.debug = debug
        self.running = False
        self.environment = Environment()

        self.command_list = {
            '': EmptyCommand,
            'exit': ExitCommand,
            'test': TestCommand
        }


    def start(self):
        self.running = True
        self.loop()


    def loop(self):

        while self.running:

            try:
                command = self.read_command()

            except ShellValidationError as e:

                print "ERROR: Command validation failed."

                if self.debug == True:
                    raise

                continue # restart loop


            if command.__class__ == ExitCommand:
                self.running = False


            try:
                print command()

            except ShellExecutionError as e:
                print "ERROR: Command execution failed."

                if self.debug is True:
                    raise


    def read_command(self):

        command_line = stdin.readline().translate(None, '\n') # read a line from stdin, remove newline
        line_segments = command_line.split(' ')
        command_key = line_segments[0]

        if not command_key in self.command_list.keys():
            raise ShellValidationError("Unknown command key '%s' used, known are: %s" % (command_key, ', '.join(self.command_list.keys())))
        
        command = self.command_list[command_key](self.environment)

        count_passed = len(line_segments) - 1
        count_expected = len(command.parameter_list)

        if count_passed != count_expected:
            raise ShellValidationError("Incorrect parameter count for command '%s'. Expected %d, got %d." % (command.__class__.__name__, count_expected, count_passed))

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
                raise ShellExecutionError("Missing parameter %d for command '%s'." % (idx, self.__class__.__name__))

        return self.execute()


    def bind_param(self, idx, value):

        if idx > (len(self.parameters) - 1):
            raise ShellValidationError("Tried to bind unkown parameter %d to command '%s'." % (idx, self.__class__.__name__))
        else:
            self.parameters[idx] = self.parameter_list[idx](value) # raises ShellValidationError on failure.


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



if __name__ == '__main__':

    shell = Shell()#debug=True)

    try:
        shell.start()

    except Exception as e:
        print "ERROR: Fatal error."

        if shell.debug == True:
            raise
        exit(1)

    exit()