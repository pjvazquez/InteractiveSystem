from transitions import Machine
from transitions.extensions import GraphMachine
from time import time, sleep
from LogUtil import get_logger
import random
import json

logger = get_logger(__name__)

with open("./Config/application.conf", "r") as confFile:
    conf = json.load(confFile)
with open("./Config/Images.conf", "r") as imgFile:
    imgs = json.load(imgFile)
'''
with open("./Config/Sequence.conf", "r") as seqFile:
    seq = json.load(seqFile)
'''

# TODO: must use declaration variables to avoid initial internal declaration
class Smile(object):
    def __init__(self):
        self.heat = False
        self.time_elapsed = False
        self.long_time_elapsed = False
        self.attempts = 0
        self.people = 0
        self.smiles = 0
        self.max_wait = 3.0
        self.message = False
        self.language = 0 # 0: cast, 1: port, 2: galego
        self.initial_time = time()
        self.initial_long_wait_time = time()
        self.max_long_wait_time = 30

    # returns True if number of detected people in fron of the camera is >= 1
    def have_people(self, event): 
        if self.people >= 1:
            have = True
        else:
            have = False
        logger.debug(f"HAVE PEOPLE - have people is {have}")
        return have

    # returns False if number of people < 1
    def dont_have_people(self, event):
        if self.people < 1:
            dont_have = True
        else:
            dont_have = False
        logger.debug(f"DONT HAVE PEOPLE - have people is {dont_have}")
        return dont_have
    
    # gets True if waiting time is over
    def elapsed_time(self, event): 
        logger.debug(f"ELAPSED TIME - Elapsed time is {self.time_elapsed}")
        return self.time_elapsed

    # gets True if waiting long time is over
    def elapsed_long_time(self, event): 
        logger.debug(f"ELAPSED LONG TIME - Elapsed long time is {self.long_time_elapsed}")
        return self.long_time_elapsed
    # gets True if waiting long time is over
    def not_elapsed_long_time(self, event): 
        logger.debug(f"ELAPSED LONG TIME - Elapsed long time is {self.long_time_elapsed}")
        return not self.long_time_elapsed

    def wait_time(self, event): 
        elapsed = time()-self.initial_time
        logger.debug(f"WAIT TIME - Elapsed time was {elapsed}")
        if elapsed >= self.max_wait:
            self.time_elapsed = True
        else:
            self.time_elapsed = False
        return self.time_elapsed

    def long_wait_time(self, event): 
        elapsed = time()-self.initial_long_wait_time
        logger.debug(f"LONG WAIT TIME - Long Time Elapsed time was {elapsed}")
        if elapsed >= self.max_long_wait_time:
            self.long_time_elapsed = True
        else:
            self.long_time_elapsed = False
        return self.long_time_elapsed


    # sets initial time value, will change in every state change
    def set_initial_time(self, event):
        self.initial_time = time()
        logger.debug(f"SET INITIAL TIME - Setting initial time value--- {self.initial_time} -----")

    # sets long initial time value, will change only when into have_people state
    def set_long_initial_time(self, event):
        self.initial_long_wait_time = time()
        logger.debug(f"SET LONG WAIT TIME - Setting initial time value--- {self.initial_time} -----")
    
    # get number of people in front of the camera
    def count_people(self, event):
        self.people = event.kwargs.get('people')
        logger.debug(f"COUNT PEOPLE - Getting number of people front --- {self.people} -----")

    # counts number of smiles and sets smiles = True if more than... 1
    def count_smiles(self, event):
        self.smiles = event.kwargs.get('smiles')
        logger.debug(F"COUNT SMILES - number of detected smiles is: {self.smiles}")
    
    # returns True if people is smiling
    def are_smiling(self, event):
        logger.debug("ARE SMILING - checks if they are smiling .... ")
        if self.smiles > 0.5:
            return True
        else:
            return False

    # returns True if people is smiling
    def are_not_smiling(self, event):
        logger.debug("ARE NOT SMILING - checks if they are smiling .... ")
        if self.smiles < 0.5:
            return True
        else:
            return False

    # show message on screen
    def show_message(self, event):
        logger.debug("SHOW MESSAGE - show message was set to true")
        self.message = True

    # returns TRue if message alrady shopwn
    def message_shown(self, event):
        logger.debug("MESSAGE SHOWN - returns message")
        return self.message

    # sets language in random 
    def set_language(self, event): 
        self.language = random.randint(0,2)
        logger.debug(F'SET LANGUAGE - set language to: {self.language}')

states=['start', 
        'initial',
        'have_people', 
        'get_people', 
        'have_smiles', 
        'get_smiles',
        'show_message', 
        'end']


states2=['start', 'wait_smiles', 'end']


transitions = [
    { # start state transition to initial
        'trigger': 'next', 
        'source': 'start', 
        'dest': 'initial', 
        'prepare': ['wait_time'], 
        'conditions': 'elapsed_time',
        'after': 'set_initial_time'
        },
    { # initial state transition to have_people, wait a bit until next one, set language (0,2)
        'trigger': 'next', 
        'source': 'initial', 
        'dest': 'have_people', 
        'prepare': ['wait_time'], 
        'conditions': 'elapsed_time', 
        'before': ['set_language'],
        'after': ['set_initial_time','set_long_initial_time']
        },
    { # have_people state transition to have smiles if we have people and after 3 seconds 
        'trigger': 'next', 
        'source': 'have_people', 
        'dest': 'have_smiles', 
        'prepare': ['count_people', 'wait_time', 'long_wait_time'], 
        'conditions': ['have_people', 'elapsed_time'], 
        'after': 'set_initial_time'
        },
    { # have_people state transition to get_people
        'trigger': 'next', 
        'source': 'have_people', 
        'dest': 'get_people', 
        'prepare': ['count_people', 'wait_time'], 
        'conditions': ['dont_have_people', 'elapsed_time'], 
        'after': 'set_initial_time'
        },
    { # get_people state transition to have_people, changing bg image
        'trigger': 'next', 
        'source': 'get_people', 
        'dest': 'have_people', 
        'conditions': 'not_elapsed_long_time',
        'after': 'set_initial_time'
        },
    { # get_people state transition to initial, changing bg image
        'trigger': 'next', 
        'source': 'get_people', 
        'dest': 'initial',
        'conditions': 'elapsed_long_time',
        'after': 'set_initial_time'
        },
    { # have_smiles state transition to get_smiles
        'trigger': 'next', 
        'source': 'have_smiles', 
        'dest': 'get_smiles', 
        'prepare': ['count_smiles', 'wait_time'], 
        'conditions': ['are_not_smiling', 'elapsed_time'], 
        'after': 'set_initial_time'
        },
    { # have_smiles state transition to show_message
        'trigger': 'next', 
        'source': 'have_smiles', 
        'dest': 'show_message', 
        'prepare': ['wait_time','count_smiles'], 
        'conditions': ['are_smiling','elapsed_time'], 
        'after': 'set_initial_time'
        },
    { # get_smiles state transition to have_smiles
        'trigger': 'next', 
        'source': 'get_smiles', 
        'dest': 'have_smiles', 
        'after': 'set_initial_time'
        },
    { # show_message state tranmsition to end
        'trigger': 'next', 
        'source': 'show_message', 
        'dest': 'end', 
        'prepare': ['show_message', 'wait_time'], 
        'conditions': ['message_shown', 'elapsed_time'], 
        'after': 'set_initial_time'
        },
    { # end state transition to initial state
        'trigger': 'next', 
        'source': 'end', 
        'dest': 'initial', 
        'prepare': ['wait_time'], 
        'conditions': 'elapsed_time', 
        'after': 'set_initial_time'
        },
]

# most complex transition sequence

transitions1 = [
    { # start state transition to initial
        'trigger': 'next', 
        'source': 'start', 
        'dest': 'initial', 
        'prepare': ['wait_time'], 
        'conditions': 'elapsed_time',
        'after': 'set_initial_time'
        },
    { # initial state transition to have_people, wait a bit until next one, set language (0,2)
        'trigger': 'next', 
        'source': 'initial', 
        'dest': 'have_people', 
        'prepare': ['wait_time'], 
        'conditions': 'elapsed_time', 
        'before': ['set_language'],
        'after': 'set_initial_time'
        },
    { # have_people state transition to have smiles if we have people and after 3 seconds 
        'trigger': 'next', 
        'source': 'have_people', 
        'dest': 'have_smiles', 
        'prepare': ['count_people', 'wait_time'], 
        'conditions': ['have_people', 'elapsed_time'], 
        'after': 'set_initial_time'
        },
    { # have_people state transition to get_people
        'trigger': 'next', 
        'source': 'have_people', 
        'dest': 'get_people', 
        'prepare': ['count_people', 'wait_time'], 
        'conditions': ['dont_have_people', 'elapsed_time'], 
        'after': 'set_initial_time'
        },
    { # get_people state transition to have_people, changing bg image
        'trigger': 'next', 
        'source': 'get_people', 
        'dest': 'have_people', 
        'after': 'set_initial_time'
        },
    { # have_smiles state transition to get_smiles
        'trigger': 'next', 
        'source': 'have_smiles', 
        'dest': 'get_smiles', 
        'prepare': ['count_smiles', 'wait_time'], 
        'conditions': ['are_not_smiling', 'elapsed_time'], 
        'after': 'set_initial_time'
        },
    { # have_smiles state transition to show_message
        'trigger': 'next', 
        'source': 'have_smiles', 
        'dest': 'show_message', 
        'prepare': ['wait_time','count_smiles'], 
        'conditions': ['are_smiling','elapsed_time'], 
        'after': 'set_initial_time'
        },
    { # get_smiles state transition to have_smiles
        'trigger': 'next', 
        'source': 'get_smiles', 
        'dest': 'have_smiles', 
        'after': 'set_initial_time'
        },
    { # show_message state tranmsition to end
        'trigger': 'next', 
        'source': 'show_message', 
        'dest': 'end', 
        'prepare': ['show_message', 'wait_time'], 
        'conditions': ['message_shown', 'elapsed_time'], 
        'after': 'set_initial_time'
        },
    { # end state transition to initial state
        'trigger': 'next', 
        'source': 'end', 
        'dest': 'initial', 
        'prepare': ['wait_time'], 
        'conditions': 'elapsed_time', 
        'after': 'set_initial_time'
        },
]


# simplest transition sequence
transitions2 = [
    { 
        'trigger': 'next', 
        'source': 'start', 
        'dest': 'wait_smiles', 
        'prepare': ['wait_time'], 
        'conditions': 'elapsed_time',
        'before': ['set_language'],
        'after': 'set_initial_time'
        },
    { 
        'trigger': 'next', 
        'source': 'wait_smiles', 
        'dest': 'end', 
        'prepare': ['count_smiles','wait_time'], 
        'conditions': ['are_smiling', 'elapsed_time' ],
        'after':'set_initial_time'
        },
    { 
        'trigger': 'next', 
        'source': 'end', 
        'dest': 'start', 
        'prepare': ['wait_time'], 
        'conditions': 'elapsed_time',
        'after': 'set_initial_time'
        },
]


def main():
    smile_ = Smile()
    machine = Machine(smile_, 
                    states=states, 
                    transitions=transitions, 
                    send_event=True, 
                    initial='start')

    for i in range(50):
        people = int(i//2.0)
        smiles = int(i//3.0)
        print("STATE--------------------------------", smile_.state, people, smiles)
        smile_.next(people=people, smiles=smiles)
        sleep(0.5)


def create_graph():
    smile_ = Smile()
    m = GraphMachine(smile_, 
                    states=states, 
                    transitions=transitions, 
                    send_event=True, 
                    show_auto_transitions=False,
                    show_conditions=True,
                    show_state_attributes=True,
                    initial='start')
    m.get_graph().draw('state_diagram_3.png', prog='dot')

if __name__ == "__main__":
    main()
