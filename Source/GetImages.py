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
from utils import get_logger

logger = get_logger(__name__)

# retrieve and parse configuration
with open("./Config/application.conf", "r") as confFile:
    conf = json.load(confFile)

imagePath = conf['image_path']

# IDEA: crate a self dictionary with images and
# return the image based on state and language


class GetImages:
    def __init__(self, statesName = 'states'):
        self.statesName = statesName
        self.bg_images = pd.DataFrame(columns=["index", "image"])
        self.languages={}
        self.imageData={}

    def getImageConf(self):
        with open("./Config/Images.conf") as imageFile:
            self.imageData = json.loads(imageFile.read())

    def generateImageDict(self):
        # loads into a dictionary all images we are going to use
        # each state has its own images
        # CHANGE this method to the new data source
        self.getImageConf()
        logger.info(f"NUM LANG ELEMENTS: {len(self.imageData)}")
        nl = 0
        for l in self.imageData.keys():
            self.languages[str(nl)]=l
            nl += 1
            for s in self.imageData[l].keys():
                for v in range(0, len(self.imageData[l][s])-1):
                    bg = cv2.imread(imagePath + self.imageData[l][s][v])
                    bg = cv2.resize(bg, (3840,2160))
                    self.bg_images.append({l+s+str(v):bg}, ignore_index=True)
        print(self.languages)
        print(self.bg_images)
    
    def getImage(self, state, lang):
        logger.info(f"Got image for -----------------{state}--{lang}")
        l = self.languages[str(lang)]
        vmax = len(self.imageData[l][state])
        v = 0
        if vmax > 1:
            v = random.randint(0,vmax-1)
        bg = cv2.imread(imagePath + self.imageData[l][state][v])
        bg = cv2.resize(bg, (3840,2160))
        return bg