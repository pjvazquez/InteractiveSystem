# coding=utf-8

import cv2
import ray
import json
import numpy as np
from datetime import datetime
from functools import wraps
from utils import draw_bounding_boxes, overlay_transparent, get_happiness, get_people
from LogUtil import get_logger
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
from TaskManagerRemote import TaskManager, ImagePredictionTask
from multiprocessing import Queue, Manager, Process
from GetImages import GetImages

from __init__ import VERSION
logger = get_logger(__name__)


# retrieve and parse configuration
with open("./Config/application.conf", "r") as confFile:
    conf = json.loads(confFile.read())

happiness_threshold = conf['happiness_threshold']
image_path = conf['image_path']

def runThreads(source=0, FiniteStateMachine = None):
    """
    Dedicated thread for grabbing video frames with VideoGet object.
    Dedicated thread for showing video frames with VideoShow object.
    Main thread serves only to pass frames between VideoGet and
    VideoShow objects/threads.
    """

    logger.info("Start video getter -----------------------")
    video_getter = VideoGet(source,(1600,900)).start()
    logger.info("Creates video window -- XXXXX NO THREAD ---------------------")
    cv2.namedWindow("Video", cv2.WND_PROP_FULLSCREEN)
    cv2.moveWindow("Video",3000,0)
    cv2.setWindowProperty("Video",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
    frame = video_getter.frame
    # cv2.imshow("Video",frame)
    logger.info("Initiated Video get and video show threads")

    # now using Ray library
    work_manager = TaskManager.remote(conf)
    work_manager.start.remote()
    logger.info("Instantiated Task Manager")

    # instantiates GetImage object
    getimages = GetImages()
    # loads data from conf file, generates language dict
    getimages.generateImageDict()
    logger.info("GET IMAGES - generated image dictionary")

    # local variables declaration
    start = time.time()
    period = 0.3
    stackLen = 5
    # stack to register last 10 detected faces and last 10 detected smiles
    faceStack = deque(maxlen=stackLen)
    smileStack = deque(maxlen=stackLen)
    people = 0
    faces = 0
    smiles = 0
    happiness = 0
    language = 0
    prev_state = None
    FSM_state = None
    detections = None

    while True:
        if (cv2.waitKey(1) == ord("q")) or video_getter.stopped:
            video_getter.stop()
            ray.shutdown()
            break

        # if defined a FSM then evolve states and returns current state
        if FiniteStateMachine is not None:
            logger.debug(F"FSM NEXT function call with STATE: {FSM_state}, smiles:{happiness}-{smileStack} and people: {faces}-{faceStack}")
            FiniteStateMachine.next(smiles=happiness, people=faces)
            language = FiniteStateMachine.language
            logger.debug(f"FSM language set to {language}")
            
            FSM_state = FiniteStateMachine.state
            logger.debug(F"FSM actual state is : {FSM_state}")
            if prev_state != FSM_state:
                logger.debug(f"New State {FSM_state} with people={people} and smiles={smiles}")
                prev_state = FSM_state
                # when states changes the system looks for a nother image to show
                logger.debug(f"FSM - Gets new image for state: {FSM_state} and language: {language}")
                new_bg = getimages.getImage(FSM_state, language)
                # if there is no new bg image, bg_image keeps the same
                if new_bg is not None:
                    bg = new_bg

        # gets frame from VideoGet thread
        # process frame in principal thread
        frame = video_getter.frame

        # it is not possible to analyze all frames, so we'll peek 
        # one frame each .3 seconds or so (3.3 frames/sec)
        if (time.time() - start) > period:
            start = time.time()
            try:
                logger.info("CALL IMAGE PREDICTION TASK")
                task = ImagePredictionTask(image=frame,result="", time=start, operation='faces')
                logger.debug("CREATES TASK AND SEND IT TO REMOTE PROCESS")
                taskRemote = ray.put(task)
                logger.debug("EXECUTES PROCESS TASK IN REMOTE")
                taskRemote = work_manager.process_task.remote(taskRemote)
                logger.debug("GETS TASK RESULT POINTER FROM REMOTE")
                task = ray.get(taskRemote)

                if task is not None:
                    detections = task.result
                    logger.debug(F"Got task result: {detections}")
                    people = get_people(detections)
                    if len(faceStack) >= stackLen:
                        faceStack.popleft()
                    faceStack.append(people)
                    logger.debug(F"Got number of people from detections: {people}")
                    if people > 0:
                        smiles = get_happiness(detections)/people
                        logger.debug(F"Got number of smiles from detections: {smiles}")
                    else:
                        smiles = 0
                    if len(smileStack) >= stackLen:
                        smileStack.popleft()
                    smileStack.append(smiles)
                    # is more efficient to accumulate measures through time
                    # to dilute moment detection problems
                    # calculates number of faces through time divided by num of elements in stack
                    faces = np.sum(faceStack)/stackLen
                    # calculates happiness as the sum of elements in stack divided by num of elements in stack
                    happiness = np.sum(smileStack)/stackLen
                    logger.debug(F"Got % of smiles from detections: {smiles} and accumulatd: {happiness}")
                else:
                    detections = None

            except Exception as err:
                traceback.print_exc()
                logger.exception(F"FACE DETECTION LOOP ERROR - {err}" )
                continue
        
        logger.info("Show result in Video Window-----------------------")
        if detections is not None:
            frame = draw_bounding_boxes(detections, frame, (255,0,0))
        frame = overlay_transparent(bg, frame,-1,0)
        # shows new frame
        cv2.imshow("Video", frame)


def main():
    ray.init()
    smile = StateManager.Smile()
    logger.info("FSM created FiniteStateMachine")
    fsm = Machine(smile, 
                states = StateManager.states, 
                transitions = StateManager.transitions,
                send_event=True, # allows to pass event values to the FSM
                initial="start")
    runThreads(source=0,FiniteStateMachine=smile )
  

if __name__ == "__main__":
    main()