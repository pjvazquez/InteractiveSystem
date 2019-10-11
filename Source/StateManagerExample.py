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
        self.max_wait = 10
        self.message = False
        self.frame = frame

    # gets True if number of detected people in fron of the camera is >= 1
    def have_people(self, frame): 
        return self.people
    
    def dont_have_people(self, frame):
        return not self.people
    
    # gets True if waiting time is over
    def time_elapsed(self, frame): 
        return self.elapsed_time
    
    # computes elapsed time and sets elapsed_time True
    def wait_time(self, frame): 
        elapsed_time = False
        init_time = time()
        while not self.elapsed_time:
            elapsed = time()-init_time
            print(elapsed)
            if elapsed >= self.max_wait:
                self.elapsed_time = True
    
    # count number of people in front of the camera
    # sets people = True if number of people > 1
    def count_people(self, frame):
        while not self.people:
            self.people = random.random() * 10 > 1
    
    # counts number of smiles and sets smiles = True if more than... 1
    def make_smile(self, frame):
        while not self.smiles:
            self.smiles = random.random() * 10 > 1
    
    # returns True if people is smiling
    def are_smiling(self, frame):
        return self.smiles

    # show message on screen
    def show_message(self, frame):
        cv2.imshow("Cap: " , frame)
        print("MESSAGE --------------------------")
        self.message = True

    # show atracting message on screen
    def show_image(self,frame):
        print("IMAGE ---------------------------")
        self.message = True

    # returns TRue if message alrady shopwn
    def message_shown(self, frame):
        return self.message

    # prints stats 
    def stats(self, frame): 
        #print('It took you some seconds')
        a = 0

states=['start', 'have_people', 'show_message', 'end']

transitions = [
    { 
        'trigger': 'next', 
        'source': 'start', 
        'dest': 'show_message', 
        'prepare': ['wait_time'], 
        'conditions': 'time_elapsed', 
        'after': 'stats'
        },
    { 
        'trigger': 'next', 
        'source': 'show_message', 
        'dest': 'end', 
        'prepare': ['show_message', 'wait_time'], 
        'conditions': 'time_elapsed', 
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


def main():
    '''
        Here is the code related withvideo capture and 
        face analysis
    '''

    video_device_id = 0
    fps = 30
    width = 640
    height = 480

    # process video
    print(cv2.__version__)
    print("Initiating vídeo capture...")

    vcap = cv2.VideoCapture(video_device_id)

    if not vcap.isOpened():
        print("[FATAL] Cant open capture device. Exitting.")
        exit(-1)
    ret, frame = vcap.read()

    # set device parameters
    vcap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    vcap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    vcap.set(cv2.CAP_PROP_FPS, fps)

    # retrieve configuration
    # this is kinda dumb...
    _width = vcap.get(cv2.CAP_PROP_FRAME_WIDTH)
    _height = vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    _fps = vcap.get(cv2.CAP_PROP_FPS)

    print()
    print("-- Camera properties -- ")
    print("  - Video id: " + str(video_device_id))
    print("  - Resolution: %dx%d" % (_width, _height))
    print("  - Fps: " + str(_fps))
    print()

    # initiate the fps thing
    start = time()
    period = 10.0 / fps

    import traceback
    import imutils
    import json

    with open("./Config/application.conf", "r") as confFile:
        conf = json.loads(confFile.read())

    '''
        Here is the code related with finite state machine
    '''
    FSMdata = {''}
    smile_ = Smile()
    machine = Machine(smile_, states, transitions=transitions, send_event=True, initial='start')

    while True:
        ret, frame = vcap.read()
        frame = imutils.resize(frame, width=width, height=height)  # resize frame

        smile_.next(data)

        print(smile_.state, smile_.are_smiling(frame))

        # if tk gui is being shown, exit by keyword press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break


def main2():
    smile_ = Smile()
    machine = Machine(smile_, states, transitions=transitions, initial='start')

    while True:
        ret, frame = vcap.read()
        frame = imutils.resize(frame, width=width, height=height)  # resize frame

        smile_.next(frame = frame)
        print(smile_.state, smile_.are_smiling(frame))


        # cv2.imshow("Cap: " + str(video_device_id), frame)

        # if tk gui is being shown, exit by keyword press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break



if __name__ == "__main__":
    main2()
