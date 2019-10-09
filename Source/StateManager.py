from transitions import Machine
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
        self.max_wait = 1
        self.message = False

    # gets True if number of detected people in fron of the camera is >= 1
    def have_people(self): 
        return self.people
    
    def dont_have_people(self):
        return not self.people
    
    # gets True if waiting time is over
    def time_elapsed(self): 
        return self.elapsed_time
    
    # computes elapsed time and sets elapsed_time True
    def wait_time(self): 
        elapsed_time = False
        init_time = time()
        while not self.elapsed_time:
            elapsed = time()-init_time
            if elapsed >= self.max_wait:
                self.elapsed_time = True
    
    # count number of people in front of the camera
    # sets people = True if number of people > 1
    def count_people(self):
        while not self.people:
            self.people = random.random() * 10 > 1
    
    # counts number of smiles and sets smiles = True if more than... 1
    def make_smile(self):
        while not self.smiles:
            self.smiles = random.random() * 10 > 1
    
    # returns True if people is smiling
    def are_smiling(self):
        return self.smiles

    # show message on screen
    def show_message(self):
        print("\n\n\n MESSAGE \n\n\n")
        self.message = True

    # show atracting message on screen
    def show_image(self):
        happyImage = cv2.imread('./Slides/happy.jpg')
        cv2.imshow("happy", happyImage)
        print("\n\n\n IMAGE \n\n\n")
        self.message = True

    # returns TRue if message alrady shopwn
    def message_shown(self):
        return self.message

    # prints stats 
    def stats(self): 
        print('It took you some seconds')

states=['start', 'have_people', 'show_message', 'wait_smiles', 'show_message', 'end']

transitions = [
    { 
        'trigger': 'next', 
        'source': 'start', 
        'dest': 'have_people', 
        'prepare': ['wait_time'], 
        'conditions': 'time_elapsed', 
        'after': 'stats'
        },
    { 
        'trigger': 'next', 
        'source': 'have_people', 
        'dest': 'wait_smiles', 
        'prepare': ['count_people', 'wait_time'], 
        'conditions': 'have_people', 
        'after': 'stats'
        },
    { 
        'trigger': 'next', 
        'source': 'have_people', 
        'dest': 'show_something', 
        'prepare': ['count_people', 'wait_time'], 
        'conditions': 'dont_have_people', 
        'after': 'stats'
        },
    { 
        'trigger': 'next', 
        'source': 'show_something', 
        'dest': 'have_people', 
        'prepare': ['show_image', 'wait_time'], 
        'conditions': 'have_people', 
        'after': 'stats'
        },
    { 
        'trigger': 'next', 
        'source': 'wait_smiles', 
        'dest': 'show_message', 
        'prepare': ['make_smile', 'wait_time'], 
        'conditions': 'are_smiling', 
        'after': 'stats'
        },
    { 
        'trigger': 'next', 
        'source': 'show_message', 
        'dest': 'end', 
        'prepare': ['show_message', 'wait_time'], 
        'conditions': ['message_shown'], 
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
