# coding=utf-8

import cv2
import ray
import json
import numpy as np
from datetime import datetime
from functools import wraps
from utils import get_logger, draw_bounding_boxes, overlay_transparent, get_happiness, get_people
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

    # stack to register last 10 emotions (5 seconds?????)
    faceStack = deque(maxlen = 10)

    logger.info("Start video getter -----------------------")
    video_getter = VideoGet(source).start()
    logger.info("Creates video window -- XXXXX NO THREAD ---------------------")
    cv2.namedWindow("Video", cv2.WND_PROP_FULLSCREEN)
    # cv2.moveWindow("Video",3000,0)
    cv2.setWindowProperty("Video",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
    frame = video_getter.frame
    # cv2.imshow("Video",frame)
    logger.info("Initiated Video get and video show threads")

    # now using Ray library
    work_manager = TaskManager.remote(conf)
    work_manager.start.remote()
    logger.info("Instantiated Task Manager")

    # loads into a dictionary all images we are going to use
    # each state has its own images
    getimages = GetImages('states2')
    bg_images = getimages.generateImageDict()
    logger.info("LOaded background images----------------------")

    start = time.time()
    period = 0.3
    people = 0
    smiles = 0
    language = 0
    prev_state = FiniteStateMachine.state
    detections = None

    while True:
        if (cv2.waitKey(1) == ord("q")) or video_getter.stopped:
            video_getter.stop()
            ray.shutdown()
            break

        # if defined a FSM then evolve states and returns current state
        if FiniteStateMachine is not None:
            FiniteStateMachine.next(smiles=smiles, people=people)
            language = FiniteStateMachine.language
            logger.info(f"FSM language set to {language}")

            img_ = FiniteStateMachine.bg_image
            logger.info(f"FSM image set to {img_}")
            
            FSM_state = FiniteStateMachine.state
            if prev_state != FSM_state:
                logger.info(f"New State {FSM_state} with people={people} and smiles={smiles}")
                prev_state = FSM_state
            # get image from bg dictionary
            bg = bg_images[FSM_state]

        # gets frame from VideoGet thread
        # process frame in principal thread
        frame = video_getter.frame

        # it is not possible to analyze all frames, so we'll peek 
        # one frame each .3 seconds or so (3.3 frames/sec)
        if (time.time() - start) > period:
            start = time.time()
            try:
                logger.info("-------------Analyzing frame")
                task = ImagePredictionTask(image=frame,result="", time=start, operation='faces')
                logger.info("-------------creates task")
                taskRemote = ray.put(task)
                logger.info(F"-------------set task in remote")
                taskRemote = work_manager.process_task.remote(taskRemote)
                # get remote result
                # taskRemote = work_manager.get_result.remote()
                task = ray.get(taskRemote)
                
                if task is not None:
                    detections = task.result
                    logger.info(F"Got result from out queue: {detections}")
                    people = get_people(detections)
                    if people > 0:
                        smiles = get_happiness(detections)/people
                    else:
                        smiles = 0
                else:
                    detections = None
            except Exception as err:
                traceback.print_exc()
                logger.exception(F"A problem while in loop: {err}" )
                continue
        
        logger.info("Show result in Video Window-----------------------")
        if detections is not None:
            frame = draw_bounding_boxes(detections, frame, (255,0,0))
        frame = overlay_transparent(bg, frame,0,0)
        # shows new framw
        cv2.imshow("Video", frame)


def main():
    ray.init()
    smile = StateManager.Smile()
    fsm = Machine(smile, 
                states = StateManager.states2, 
                transitions = StateManager.transitions2,
                send_event=True, # allows to pass event values to the FSM
                initial="start")
    runThreads(source=0,FiniteStateMachine=smile )
  

if __name__ == "__main__":
    main()