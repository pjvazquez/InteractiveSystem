# coding=utf-8

import logging
import sys
import time
import cv2

from __init__ import DEFAULT_LOGGING_LEVEL


def get_logger(name, level=DEFAULT_LOGGING_LEVEL):

    logger = logging.getLogger(name)
    logger.setLevel(level)

    ch = logging.StreamHandler(sys.stdout)
    # TODO: use a rotatingFileHandler in the deployment mode

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    logger.addHandler(ch)

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
