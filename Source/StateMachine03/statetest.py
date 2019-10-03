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
import argparse
import json
import inspect
#from transitions import Machine, State
from transitions import Machine


Cmd_line_options = None


class ConvertString(object):
    """FSM which converts strings.  Characters inside double quotes
    are converted to upper case.
    """

    states = ['start', 'in_quotes', 'not_in_quotes', 'error', 'end', ]

    def __init__(self):
        self.machine = Machine(
            model=self,
            states=self.states,
            initial='start')
        self.machine.add_transition(        # Rule no. 1
            trigger='feed_char',
            source='start',
            dest='in_quotes',
            #after='print_char_upper',
            conditions=[self.is_quote])
        self.machine.add_transition(        # Rule no. 2
            trigger='feed_char',
            source='start',
            dest='not_in_quotes',
            after='print_char',
            conditions=[self.is_not_quote])
        self.machine.add_transition(        # Rule no. 3
            trigger='feed_char',
            source='in_quotes',
            dest='not_in_quotes',
            #after='print_char_upper',
            conditions=[self.is_quote])
        self.machine.add_transition(        # Rule no. 4
            trigger='feed_char',
            source='in_quotes',
            dest='in_quotes',
            after='print_char_upper',
            conditions=[self.is_not_quote])
        self.machine.add_transition(        # Rule no. 5
            trigger='feed_char',
            source='not_in_quotes',
            dest='not_in_quotes',
            after='print_char',
            conditions=[self.is_not_quote])
        self.machine.add_transition(        # Rule no. 6
            trigger='feed_char',
            source='not_in_quotes',
            dest='in_quotes',
            #after='print_char',
            conditions=[self.is_quote])
        self.machine.add_transition(        # Rule no. 7
            trigger='feed_char',
            source='in_quotes',
            dest='error',
            after=[self.print_status, self.exit],
            conditions=[self.is_eof])
        self.machine.add_transition(        # Rule no. 8
            trigger='feed_char',
            source='not_in_quotes',
            dest='end',
            after='print_status',
            conditions=[self.is_eof])

    def is_quote(self, char):
        """Return True if char is not end of input char and is quote char."""
        result = True if char != '$' and char == '"' else False
        dbgprint('(is_quote) char: {}  result: {}'.format(char, result))
        return result

    def is_not_quote(self, char):
        """Return True if char is not end of input char and not quote char."""
        result = True if char != '$' and char != '"' else False
        dbgprint('(is_quote) char: {}  result: {}'.format(char, result))
        return result

    def is_eof(self, char):
        """Return True if current char is the end of input character."""
        dbgprint('(is_eof) char: {}'.format(char))
        return True if char == '$' else False

    def print_char(self, char):
        """Print the current char unchanged."""
        print('char: {}'.format(char))

    def print_char_upper(self, char):
        """Convert the char to upper-case and print it."""
        print('char: {}'.format(char.upper()))

    def print_status(self, char):
        """Print the current status (state, char) of the FSM."""
        print('status -- state: {}  char: {}'.format(self.state, char))

    def exit(self, char):
        sys.exit('finished')


def dbgprint(msg):
    if Cmd_line_options.verbose:
        print(msg)


def run(machine):
    for char in Cmd_line_options.data:
        machine.feed_char(char)


def show(machine):
    print('machine: {}'.format(machine))


def to_json(model):
    machine = model.machine
    jobj = {}
    jobj['model-class-name'] = model.__class__.__name__
    jobj['states'] = list(machine.states)
    jobj['initial-state'] = machine.initial
    jtransitions = []
    items = []
    #callbacknames = []
    for key, event in machine.events.items():
        if not key.startswith('to_'):
            items.append((key, event))
    for key, event in items:
        for tr_name, transitions in event.transitions.items():
            for transition in transitions:
                funcs = []
                for condition in transition.conditions:
                    funcs.append(condition.func.__name__)
                jtransition = {
                    'trigger': key,
                    'source': transition.source,
                    'dest': transition.dest,
                    'conditions': funcs,
                }
                if transition.before:
                    names = collect_names(transition.before)
                    jtransition['before'] = names
                    #callbacknames.extend(names)
                if transition.after:
                    names = collect_names(transition.after)
                    jtransition['after'] = names
                    #callbacknames.extend(names)
                if transition.prepare:
                    names = collect_names(transition.prepare)
                    jtransition['prepare'] = names
                    #callbacknames.extend(names)
                jtransitions.append(jtransition)
    jobj['transitions'] = jtransitions
    members = inspect.getmembers(model, inspect.ismethod)
    jcallbacks = []
    for callbackname, callback in members:
        if callbackname == '__init__':
            continue
        # pull out the method name, the parameters, and code body.
        # look at IPython implementation for help.
        source = inspect.getsource(callback)
        jcallback = {
            'name': callbackname,
            'source': source,
        }
        jcallbacks.append(jcallback)
    jobj['callbacks'] = jcallbacks
    json.dump(jobj, sys.stdout)
    print()


def collect_names(callbacks):
    names = []
    for callback in callbacks:
        if isinstance(callback, str):
            names.append(callback)
        else:
            names.append(callback.__name__)
    return names


Function_map = {
    'run': run,
    'show': show,
    'to_json': to_json,
}


def main():
    global Cmd_line_options
    description = """\
synopsis:
  a test platform for FSMs defined with `transistions`.
"""
    epilog = """\
commands:
    run --     Run the FSM on the data (a character string).
               Converts characters inside double quotes to upper case.
    show --    Print out the FSM.
    to_json -- Produce a JSON representation of the FSM.
               Write it to stdout.

examples:
  python transitions-test01.py run "some \"input\" string"
  python transitions-test01.py show
  python transitions-test01.py to_json > output.json
"""
    parser = argparse.ArgumentParser(
        description=description,
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "command",
        help="Command: one of ['run', 'show', 'to_json']"
    )
    parser.add_argument(
        "data",
        help="Data: a string of characters"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print additional info while running"
    )
    options = parser.parse_args()
    Cmd_line_options = options
    fn = Function_map.get(options.command)
    if fn is not None:
        machine = ConvertString()
        fn(machine)
    else:
        parser.error('invalid command: {}'.format(options.command))


if __name__ == '__main__':
    #import ipdb; ipdb.set_trace()
    main()