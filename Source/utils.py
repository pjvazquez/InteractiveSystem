# coding=utf-8

import logging
from logging.handlers import RotatingFileHandler
import sys
import time
import cv2
import math
import numpy as np

from __init__ import DEFAULT_LOGGING_LEVEL


def get_logger(name, level=DEFAULT_LOGGING_LEVEL):

    from datetime import datetime

    logger = logging.getLogger(name)
    logger.setLevel(level)

    ch0 = logging.StreamHandler(sys.stdout)
    ch0.setLevel(level)
    ch1 = RotatingFileHandler('./Logs/interactiveSystem.log', maxBytes=5000000, backupCount=10)
    ch1.setLevel(level)
    # TODO: use a rotatingFileHandler in the deployment mode

    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
    ch0.setFormatter(formatter)
    ch1.setFormatter(formatter)

    logger.addHandler(ch0)
    logger.addHandler(ch1)

    return logger


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' % (method.__name__, (te - ts) * 1000))
        return result

    return timed


def draw_bounding_box(_face_coordinates, image_array, color):
    try:
        _face_coordinates = (
            _face_coordinates["x"], _face_coordinates["y"], _face_coordinates["h"], _face_coordinates["w"])
        x, y, w, h = _face_coordinates
        cv2.rectangle(image_array, (x, y), (x + w, y + h), color, 2)
    except Exception:
        print(Exception)

def draw_bounding_boxes(detections, frame, color):
    try:
        for face in detections["analyzed_faces"]:
            face_coordinates = face["coordinates"]
            draw_bounding_box(face_coordinates, frame, color)
    except Exception:
        print(Exception)

    return frame



def draw_label(image, point, label, font=cv2.FONT_HERSHEY_SIMPLEX,
                font_scale=1., thickness=2):
    size = cv2.getTextSize(label, font, font_scale, thickness)[0]
    x, y = point
    cv2.rectangle(image, (x, y - size[1]), (x + size[0], y), (255, 0, 0), cv2.FILLED)
    cv2.putText(image, label, point, font, font_scale, (255, 255, 255), thickness)


def overlay_transparent(background, overlay, x, y):
    # as a little trick, if x and/or y is negative
    # I can set x and y as left or down....

    background_width = background.shape[1]
    background_height = background.shape[0]

    if x >= background_width or y >= background_height:
        return background

    h, w = overlay.shape[0], overlay.shape[1]

    if x == -1 :
        x = background_width - w -1
    
    if y == -1:
        y = background_height - h - 1

    if x + w > background_width:
        w = background_width - x
        overlay = overlay[:, :w]

    if y + h > background_height:
        h = background_height - y
        overlay = overlay[:h]

    if overlay.shape[2] < 4:
        overlay = np.concatenate(
            [
                overlay,
                np.ones((overlay.shape[0], overlay.shape[1], 1), dtype = overlay.dtype) * 255
            ],
            axis = 2,
        )

    overlay_image = overlay[..., :3]
    mask = overlay[..., 3:] / 255.0

    background[y:y+h, x:x+w] = (1.0 - mask) * background[y:y+h, x:x+w] + mask * overlay_image

    return background

def get_happiness(detections = None):
    happiness = 0
    for face in detections["analyzed_faces"]:
        if "emotions" in face and face["emotions"] is not None:
            happiness += int(math.ceil(face["emotions"]["happy"]))
    return happiness

def get_people(detections = None):
    return len(detections["analyzed_faces"])
