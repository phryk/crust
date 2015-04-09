# -*- coding: utf-8 -*-
from sys import stdin


class Shell(object):

    debug = None
    running = None


    def __init__(self, debug=False):

        self.debug = debug
        self.running = False


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



