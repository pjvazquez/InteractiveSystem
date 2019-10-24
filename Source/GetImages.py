# coding=utf-8

import json
import math
import traceback
import imutils
import StateManager
import random
import time
import utils
import cv2
import pandas as pd
from __init__ import VERSION
from LogUtil import get_logger

logger = get_logger(__name__)

# retrieve and parse configuration
with open("./Config/application.conf", "r") as confFile:
    conf = json.load(confFile)

imagePath = conf['image_path']


# IDEA: crate a self dictionary with images and
# return the image based on state and language


class GetImages:
    def __init__(self):
        self.bg_images = pd.DataFrame(columns=["index", "image"])
        self.languages={}
        self.imageData={}
        self.relatedStates = []
        self.v = 0
        self.previousState = None
        self.previousImage = None

    def getImageConf(self):
        logger.debug("Reading image configuration from Images.conf")
        with open("./Config/Images.conf") as imageFile:
            conf = json.loads(imageFile.read())
            
        self.imageData = conf['imageState']
        self.relatedStates = conf['relatedStates']
        logger.debug(f"Got ImageData: {self.imageData}")
        logger.debug(f"Got relatedSates: {self.relatedStates}")

    def generateImageDict(self):
        # loads into a dictionary all images we are going to use
        # each state has its own images
        # CHANGE this method to the new data source
        self.getImageConf()
        logger.debug(f"NUM LANG ELEMENTS: {len(self.imageData)}")
        nl = 0
        for l in self.imageData.keys():
            self.languages[str(nl)]=l
            nl += 1
            '''
            for s in self.imageData[l].keys():
                for v in range(0, len(self.imageData[l][s])-1):
                    logger.info(f"Image path: {imagePath + str(l)}/{self.imageData[l][s][v]}")
                    bg = cv2.imread(imagePath + str(l) +"/" + self.imageData[l][s][v])
                    bg = cv2.resize(bg, (3840,2160))
                    self.bg_images.append({l+s+str(v):bg}, ignore_index=True)'''
        # print(self.languages)
        # print(self.bg_images)
    
    def getImage(self, state, lang):
        l = self.languages[str(lang)]
        logger.info(f"Got image for -----------------{state}--{lang}:{l}")
        if state in self.imageData[l].keys():
            # if the new state and the previous state are related then do not generate a new rand val
            # condition must cover all possibilities
            if self.previousState is not None and self.previousState in self.relatedStates and state in self.relatedStates:
                logger.debug(f"RELATED Image path: {imagePath + l}/{self.imageData[l][state][self.v]}")
                bg = cv2.imread(imagePath + l +"/" + self.imageData[l][state][self.v])
                logger.debug(f"RELATED Image shape: {bg.shape}")
                bg = cv2.resize(bg, (3840,2160))            
            else:
                vmax = len(self.imageData[l][state])
                self.v = 0
                if vmax > 1:
                    new_v = random.randint(0,vmax-1)
                    if self.v == new_v:
                        self.v = int((new_v+1)%vmax)
                else:
                    self.v = 0
                logger.debug(f"Image path: {imagePath + l}/{self.imageData[l][state][self.v]}")
                bg = cv2.imread(imagePath + l +"/" + self.imageData[l][state][self.v])
                logger.debug(f"Image shape: {bg.shape}")
                bg = cv2.resize(bg, (3840,2160))
            self.previousState = state
            return bg
        else:
            return None