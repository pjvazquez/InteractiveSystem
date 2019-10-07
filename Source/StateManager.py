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

if __name__ == "__main__":
    '''
        Here is the code related with video capture and 
        face analysis
    '''

    video_device_id = 0
    fps = 60
    width = 1920
    height = 1080

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

    cv2.namedWindow("window", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("window",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)


    def draw_bounding_box(_face_coordinates, image_array, color):
        _face_coordinates = (
            _face_coordinates["x"], _face_coordinates["y"], _face_coordinates["h"], _face_coordinates["w"])
        x, y, w, h = _face_coordinates
        cv2.rectangle(image_array, (x, y), (x + w, y + h), color, 2)


    def draw_label(image, point, label, font=cv2.FONT_HERSHEY_SIMPLEX,
                   font_scale=1., thickness=2):
        size = cv2.getTextSize(label, font, font_scale, thickness)[0]
        x, y = point
        cv2.rectangle(image, (x, y - size[1]), (x + size[0], y), (255, 0, 0), cv2.FILLED)
        cv2.putText(image, label, point, font, font_scale, (255, 255, 255), thickness)


    import json
    import math
    import traceback
    import imutils
    import numpy as np
    from collections import deque
    from FaceAnalyzer import FaceAnalyzer

    # from elasticsearch import Elasticsearch

    # stack to register last 10 emotions (5 seconds?????)
    faceStack = deque(maxlen = 10)

    with open("./Config/application.conf", "r") as confFile:
        conf = json.loads(confFile.read())

    happiness_threshold = conf['happiness_threshold']

    processor = FaceAnalyzer(None, 
                            None,
                            identify_faces=False,
                            detect_ages=False,
                            detect_emotions=True,
                            detect_genders=False,
                            face_detection_upscales=0)

    '''
        Here is the code related with phinite state machine
    '''
    smile_ = Smile()
    machine = Machine(smile_, states, transitions=transitions, initial='start')
    '''
    for i in range(0,50):
        print("iteration: {}".format(i) , "\tState: ", smile_.state, smile_.people, smile_.smiles )
        smile_.next()
    '''

    while True:
        ret, frame = vcap.read()
        frame = imutils.resize(frame, width=width, height=height)  # resize frame

        if (time() - start) > period:
            start += period

            start_time = time()
            try:
                detections = processor.analyze_frame(frame)
            except Exception:
                traceback.print_exc()
                continue

            if detections:
                # noinspection PyTypeChecker
                for face in detections["analyzed_faces"]:
                    face_coordinates = face["coordinates"]
                    draw_bounding_box(face_coordinates, frame, (255, 0, 0))
                    y_offset = 10
                    if "emotions" in face and face["emotions"] is not None:
                        y_offset += 10
                        for _label in ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']:
                            emotion_value = int(math.ceil(face["emotions"][_label] * 10))
                            if _label == 'happy':
                                if len(faceStack) >= 10:
                                    faceStack.popleft()
                                faceStack.append(emotion_value)
                                happiness = np.sum(faceStack)
                                # print(happiness, faceStack)
                                if happiness > happiness_threshold:
                                    happyImage = cv2.imread('./Slides/happy.jpg')
                                    cv2.imshow("happy", happyImage)
                                    cv2.putText(frame, "MOLA", (100,100), cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 255, 255), 4)

            # DEPENDS IF IT IS HERE OR OU THE if, BEHAVIOUR IS A BIT DIFFERENT        
            smile_.next()
            cv2.imshow("window", frame)
            # out.write(frame)

        # if tk gui is being shown, exit by keyword press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break



    
    '''
    # This code is to generate the FSM graph
    from transitions.extensions import GraphMachine
    extra_args = dict(initial='start', title='Smile transitions!',show_conditions=True, show_state_attributes=True)
    m = GraphMachine(model=smile_, states=states, transitions=transitions, show_auto_transitions=False,**extra_args)
    m._get_graph(model=smile_).draw("state_diagram.png", prog='dot')
    '''