#!/usr/bin/env python

"""
usage: transitions_test04.py [-h] [-v] command data

synopsis:
  a test platform for FSMs defined with `transistions`.

positional arguments:
  command        Command: one of ['run', 'show', 'to_json']
  data           Data: a string of characters

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Print additional info while running

commands:
    run --     Run the FSM on the data (a character string).
               Converts characters inside double quotes to upper case.
    show --    Print out the FSM.
    to_json -- Produce a JSON representation of the FSM.
               Write it to stdout.

examples:
  python transitions-test04.py run "some \"input\" string"
  python transitions-test04.py show
  python transitions-test04.py to_json > output.json
developper:
  http://davekuhlman.org/fsm-transitions-python.html
"""


from __future__ import print_function
import sys
import time
#from transitions import Machine, State
from transitions import Machine


Cmd_line_options = None


class Interact(object):
    """
    FSM that runs when some conditions are ok
    """

    states = ['start', 'have_people', 'wait_smiles', 'show_message', 'show_something','end', ]

    def __init__(self):
        self.machine = Machine(
            model=self,
            states=self.states,
            initial='start')

        self.machine.add_transition(
            trigger='start_show',
            source='start',
            dest='wait_smiles',
            after='print_status',
            conditions=[self.is_time])
        self.machine.add_transition(
            trigger='wait_smiles',
            source='start_show',
            dest='end',
            after='print_status',
            conditions=[self.is_time])
        self.machine.add_transition(
            trigger='end',
            source='wait_smiles',
            dest='start',
            after='print_status',
            #conditions=[self.is_eof]
            )

    def is_time(self, waiting_time = 1):
        """Return True if char is not end of input char and is quote char."""
        initial_time = time.time()
        elapsed = 0
        while elapsed < waiting_time:
            elapsed = time.time() - initial_time
            # print(elapsed)

        return True

    def print_status(self):
        print(self.state)

    def exit(self, char):
        sys.exit('finished')



if __name__ == '__main__':
    machine = Interact()
    print('object created')
    machine.start_show()
    print('start show')
    machine.wait_smiles()