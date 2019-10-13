# coding=utf-8

import cv2
import json
import numpy as np
from datetime import datetime
from functools import wraps
from __init__ import VERSION
from utils import get_logger
import FaceAnalyzer as fa
from VideoGet import VideoGet
from VideoShow import VideoShow
import math
import traceback
import imutils
from collections import deque
from FaceAnalyzer import FaceAnalyzer
import StateManager
from transitions import Machine
import time
import utils
from TaskManager import TaskManager, ImagePredictionTask
from multiprocessing import Queue

logger = get_logger(__name__)


# retrieve and parse configuration
with open("./Config/application.conf", "r") as confFile:
    conf = json.loads(confFile.read())

# happiness_threshold = conf('happiness_threshold')

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
    logger.info("Initiated Video get and video show threads")

    # instead of this, we arer going to use an independent process
    '''
    face_analyzer = FaceAnalyzer(None, 
                            None,
                            identify_faces=False,
                            detect_ages=False,
                            detect_emotions=True,
                            detect_genders=False,
                            face_detection_upscales=0)
    '''

    work_manager = TaskManager(conf)
    logger.info("Instantiated Task Manager")
    work_manager.start()
    logger.info("initiated task manager")

    # loads into a dictionary all images we are going to use
    # each state has its own images
    bg_images = {}
    for i, state in enumerate(StateManager.states):
        bg = cv2.imread(f'Slides/Diapositiva{i%5+1}.png')
        bg_images[state] = cv2.resize(bg,(3840,2160))

    start = time.time()
    period = 0.3
    people = 0
    smiles = 0
    prev_state = FiniteStateMachine.state

    while True:
        if video_getter.stopped or video_shower.stopped:
            video_shower.stop()
            video_getter.stop()
            work_manager.stop()
            break

        # if defined a FSM then evolve states and returns current state
        if FiniteStateMachine is not None:
            FiniteStateMachine.next(smiles=smiles, people=people)
            FSM_state = FiniteStateMachine.state
            if prev_state != FSM_state:
                logger.info(f"New State {FSM_state} with people={people} and smiles={smiles}")
                prev_state = FSM_state

            bg = bg_images[FSM_state]

        # gets frame from VideoGet thread
        frame = video_getter.frame
        # process frame in principal thread

        # is this frame nedded to be processed?
        if (time.time() - start) > period:
            start = time.time()
            try:
                logger.info("-------------Analyzing frame")
                task = ImagePredictionTask(image=frame,result="", time=start, operation='faces')
                logger.info("-------------creates task")
                work_manager.enqueue(task)
                logger.info("-------------put task in queue")
                # using TaskManger to try to use anotehr process for image processing
                detections = (work_manager.dequeue()).result
                logger.info(F"got result from out queue: {detections}")
                people = utils.get_people(detections)
                if people > 0:
                    smiles = utils.get_happiness(detections)/people
                else:
                    smiles = 0

            except Exception:
                traceback.print_exc()
                logger.exception("A problem whike in loop")
                continue
        #frame = utils.draw_bounding_boxes(detections, frame, (255,0,0))
        frame = utils.overlay_transparent(bg, frame,0,0)
        # sets frame in VideoShow frame
        video_shower.frame = frame


def main():
    smile = StateManager.Smile()
    fsm = Machine(smile, 
                states = StateManager.states2, 
                transitions = StateManager.transitions2,
                send_event=True, # allows to pass event values to the FSM
                initial="start")
    runThreads(source=0,FiniteStateMachine=smile )
  




if __name__ == "__main__":
    with open("./Config/application.conf", "r") as confFile:
        conf = json.loads(confFile.read())
    happiness_threshold = conf['happiness_threshold']
    main()