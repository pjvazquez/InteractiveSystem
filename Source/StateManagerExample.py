from transitions import Machine
from transitions.extensions import GraphMachine
import random
import cv2
from time import time


# TODO: must use declaration variables to avoid initial internal declaration
class Smile(object):
    def __init__(self):
        self.heat = False
        self.elapsed_time = False
        self.attempts = 0
        self.people = 0
        self.smiles = 0
        self.some_value = 0
        self.max_wait = 3
        self.message = False

    # gets True if number of detected people in fron of the camera is >= 1
    def have_people(self, event): 
        print("check have people.....")
        if self.people >= 1:
            return True
        return False
    
    def dont_have_people(self, event):
        return not self.people
    
    # gets True if waiting time is over
    def time_elapsed(self, event): 
        print("check time elapsed")
        return self.elapsed_time
    
    # computes elapsed time and sets elapsed_time True
    def wait_time(self, event):
        print("init wait time")
        self.elapsed_time = False
        init_time = time()
        while not self.elapsed_time:
            elapsed = time()-init_time
            if elapsed >= self.max_wait:
                self.elapsed_time = True
                print("elapsed time: ", elapsed)

    
    # count number of people in front of the camera
    # sets people = True if number of people > 1
    def count_people(self, event):
        self.people = event.kwargs.get('people')
        print("counting people-------have: ", self.people)
    
    # counts number of smiles and sets smiles = True if more than... 1
    def make_smile(self, event):
        while not self.smiles:
            print("making smiles --------")
    
    # returns True if people is smiling
    def are_smiling(self, event):
        return self.smiles

    # show message on screen
    def show_message(self, event):
        print("MESSAGE --------------------------")
        self.message = True

    # show atracting message on screen
    def show_image(self,event):
        print("IMAGE ---------------------------")
        self.message = True

    # returns TRue if message alrady shopwn
    def message_shown(self, event):
        return self.message

    # prints stats 
    def stats(self, event): 
        #print('It took you some seconds')
        self.elapsed_time = False

    def change_some_value(self,event):
        self.some_value = random.randint(1, 20)

states2=['start', 'have_people', 'wait_people', 'end']

transitions2 = [
    { 
        'trigger': 'next', 
        'source': 'start', 
        'dest': 'have_people', 
        'prepare': ['wait_time'], 
        'conditions': 'time_elapsed', 
        'before': 'change_some_value',
        'after': 'stats'
        },
    { 
        'trigger': 'next', 
        'source': 'have_people', 
        'dest': 'end',
        'prepare': ['count_people', 'wait_time'], 
        'conditions': ['have_people','time_elapsed'], 
        'before': 'change_some_value',
        'after': 'stats'
        },
    { 
        'trigger': 'next', 
        'source': 'have_people', 
        'dest': 'wait_people',
        'prepare': ['wait_time'], 
        'conditions': ['time_elapsed'], 
        'before': 'change_some_value',
        'after': 'stats'
        },
    { 
        'trigger': 'next', 
        'source': 'wait_people', 
        'dest': 'end', 
        'prepare': ['count_people', 'wait_time'], 
        'conditions': ['have_people','time_elapsed'], 
        'before': 'change_some_value',
        'after': 'stats'
        },
    { 
        'trigger': 'next', 
        'source': 'end', 
        'dest': 'start', 
        'prepare': ['wait_time'], 
        'conditions': 'time_elapsed', 
        'before': 'change_some_value',
        'after': 'stats'
        },
]

states=['start', 
        'initial',
        'have_people', 
        'get_people', 
        'have_smiles', 
        'get_smiles',
        'show_message', 
        'end']

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
    { # end state transition to initial state
        'trigger': 'next', 
        'source': 'end', 
        'dest': 'initial', 
        'prepare': ['wait_time'], 
        'conditions': 'time_elapsed', 
        'after': 'set_bg'
        },
]

def main():
    smile_ = Smile()
    machine = Machine(smile_, 
                    states=states2, 
                    transitions=transitions2, 
                    send_event=True, 
                    initial='start')

    for i in range(10):
        people = int(i%2.0)
        smiles = int(i%2.0)
        print("STATE--------------------------------", smile_.state, people, smiles, smile_.some_value)
        smile_.next(people=people, smiles=smiles)


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
    m.get_graph().draw('state_diagram_1.png', prog='dot')

if __name__ == "__main__":
    create_graph()
