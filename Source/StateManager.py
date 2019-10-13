from transitions import Machine
from time import time
from utils import get_logger
import random


logger = get_logger(__name__)

# TODO: must use declaration variables to avoid initial internal declaration
class Smile(object):
    def __init__(self):
        self.heat = False
        self.time_elapsed = False
        self.attempts = 0
        self.people = 0
        self.smiles = 0
        self.max_wait = 3
        self.message = False
        self.language = 0 # 0: cast, 1: port, 2: galego
        self.bg_image = []

    # returns True if number of detected people in fron of the camera is >= 1
    def have_people(self, event): 
        if self.people >= 1:
            return True
        else:
            return False

    # returns False if number of people < 1
    def dont_have_people(self, event):
        if self.people < 1:
            return True
        else:
            return False
    
    # gets True if waiting time is over
    def elapsed_time(self, event): 
        return self.time_elapsed
    
    # computes elapsed time and sets elapsed_time True
    def wait_time(self, event): 
        logger.info("waiting time---------")
        self.time_elapsed = False
        init_time = time()
        while not self.time_elapsed:
            elapsed = time()-init_time
            if elapsed >= self.max_wait:
                self.time_elapsed = True
                logger.info("time elapsed--------------")
    
    # get number of people in front of the camera
    
    def count_people(self, event):
        self.people = event.kwargs.get('people')
    
    # counts number of smiles and sets smiles = True if more than... 1
    def count_smile(self, event):
        self.smiles = event.kwargs.get('smiles')
        logger.info(F"MAKE SMILE++++{self.smiles}")
    
    # returns True if people is smiling
    def are_smiling(self, event):
        logger.info("checks if they are smiling .... ")
        if self.smiles > 1:
            return True
        else:
            return False

    # show message on screen
    def show_message(self, event):
        logger.info("++++++++++++MESSAGE")
        self.message = True

    # show atracting message on screen
    def set_bg(self, event):
        logger.info("-----------------------------sets background image")
        self.bg_image = random.randint(0,3)

    # returns TRue if message alrady shopwn
    def message_shown(self, event):
        return self.message

    # sets language in random 
    def set_language(self, event): 
        self.language = random.randint(0,2)
        logger.info('set language to: ' self.language)

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
    { # start state transition to initial, nothing to do except preparing
        'trigger': 'next', 
        'source': 'start', 
        'dest': 'initial', 
        'prepare': ['wait_time'], 
        'conditions': 'elapsed_time', 
        'after': 'set_bg'
        },
    { # initial state transition to have_people, wait a bit until next one, set language (0,2)
        'trigger': 'next', 
        'source': 'initial', 
        'dest': 'have_people', 
        'prepare': ['wait_time'], 
        'conditions': 'elapsed_time', 
        'before': ['set_language'],
        'after': 'set_bg'
        },
    { # have_people state transition to have smiles if we have people and after 3 seconds 
        'trigger': 'next', 
        'source': 'have_people', 
        'dest': 'have_smiles', 
        'prepare': ['count_people', 'wait_time'], 
        'conditions': ['have_people', 'elapsed_time'], 
        'after': 'set_bg'
        },
    { # have_people state transition to get_people
        'trigger': 'next', 
        'source': 'have_people', 
        'dest': 'get_people', 
        'prepare': ['count_people', 'wait_time'], 
        'conditions': ['dont_have_people', 'elapsed_time'], 
        'after': 'set_bg'
        },
    { # get_people state transition to have_people, changing bg image
        'trigger': 'next', 
        'source': 'get_people', 
        'dest': 'have_people', 
        'after': 'set_bg'
        },
    { # have_smiles state transition to get_smiles
        'trigger': 'next', 
        'source': 'have_smiles', 
        'dest': 'get_smiles', 
        'prepare': ['count_smiles', 'wait_time'], 
        'conditions': ['are_not_smiling', 'elapsed_time'], 
        'after': 'set_bg'
        },
    { # have_smiles state transition to show_message
        'trigger': 'next', 
        'source': 'have_smiles', 
        'dest': 'show_message', 
        'prepare': ['wait_time','count_smiles'], 
        'conditions': ['are_smiling','elapsed_time'], 
        'after': 'set_bg'
        },
    { # get_smiles state transition to have_smiles
        'trigger': 'next', 
        'source': 'get_smiles', 
        'dest': 'have_smiles', 
        'after': 'set_bg'
        },
    { # show_message state tranmsition to end
        'trigger': 'next', 
        'source': 'show_message', 
        'dest': 'end', 
        'prepare': ['show_message', 'wait_time'], 
        'conditions': ['message_shown', 'elapsed_time'], 
        'after': 'set_bg'
        },
    { ~# end state transition to initial state
        'trigger': 'next', 
        'source': 'end', 
        'dest': 'initial', 
        'prepare': ['wait_time'], 
        'conditions': 'time_elapsed', 
        'after': 'set_bg'
        },
]

transitions2 = [
    { 
        'trigger': 'next', 
        'source': 'start', 
        'dest': 'wait_smiles', 
        'prepare': ['wait_time'], 
        'conditions': 'time_elapsed', 
        'after': 'stats'
        },
    { 
        'trigger': 'next', 
        'source': 'wait_smiles', 
        'dest': 'end', 
        'prepare': ['make_smile'], 
        'conditions': 'are_smiling', 
        'after': 'stats'
        },
    { 
        'trigger': 'next', 
        'source': 'end', 
        'dest': 'start', 
        'prepare': ['wait_time'], 
        'conditions': 'time_elapsed', 
        'after': 'stats'
        },
]
