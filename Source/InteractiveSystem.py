# coding=utf-8

import cv2
import json
import numpy as np
from datetime import datetime
from functools import wraps
from __init__ import VERSION
from utils import get_logger
import FaceAnalyzer as fa
from videoget import VideoGet
from videoshow import VideoShow
import math
import traceback
import imutils
from collections import deque

logger = get_logger(__name__)


# retrieve and parse configuration
with open("../Config/application.conf", "r") as confFile:
    conf = json.loads(confFile.read())

happiness_threshold = conf('happiness_threshold')

def runThreads(source=0, FiniteStateMachine = None):
    """
    Dedicated thread for grabbing video frames with VideoGet object.
    Dedicated thread for showing video frames with VideoShow object.
    Main thread serves only to pass frames between VideoGet and
    VideoShow objects/threads.
    """

    # stack to register last 10 emotions (5 seconds?????)
    faceStack = deque(maxlen = 10)

    video_getter = VideoGet(source).start()
    video_shower = VideoShow(video_getter.frame).start()
    cps = CountsPerSec().start()

    bg = np.asarray(cv2.imread('img/Diapositiva1.png'))
    bg = cv2.resize(bg,(3840,2160))

    processor = fa.FaceAnalyzer(None, 
                        None,
                        identify_faces=False,
                        detect_ages=False,
                        detect_emotions=True,
                        detect_genders=False,
                        face_detection_upscales=0)

    while True:
        if video_getter.stopped or video_shower.stopped:
            video_shower.stop()
            video_getter.stop()
            break

        # if defined a FSM then evolve states and returns current state
        if FiniteStateMachine is not None:
            FiniteStateMachine.next()
            FSM_state = FiniteStateMachine.state
        
        # gets frame from VideoGet thread
        frame = video_getter.frame
        # process frame in principal thread

        # is this frame nedded to be processed?
        if (time.time() - start) > period:
            start += period

            start_time = time.time()
            try:
                detections = processor.analyze_frame(frame)
            except Exception:
                traceback.print_exc()
                continue
            # print("Done in %s seconds" % (time.time() - start_time))


        frame = overlay_transparent(bg, frame,0,0)
        frame = putState(frame, FSM_state)
        # sets frame in VideoShow frame
        video_shower.frame = frame



def main():
    smile = Smile()
    fsm = Machine(smile, 
                states = StateManager.states, 
                transitions = StateManager.transitions,
                initial="start")
    runThreads(source=0,FiniteStateMachine=smile )
  




if __name__ == "__main__":
    with open("./Config/application.conf", "r") as confFile:
        conf = json.loads(confFile.read())
    happiness_threshold = conf['happiness_threshold']

    main()