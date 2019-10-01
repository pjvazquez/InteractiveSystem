# coding=utf-8

import cv2
import json
import numpy as np
from datetime import datetime
from functools import wraps
from __init__ import VERSION
from utils import get_logger
import FaceAnalyzer as fa


logger = get_logger(__name__)


# retrieve and parse configuration
with open("../Config/application.conf", "r") as confFile:
    conf = json.loads(confFile.read())

happiness_threshold = conf('happiness_threshold')

if __name__ == "__main__":

    video_device_id = 0
    fps = 30
    width = 640
    height = 480

    # process video
    print(cv2.__version__)
    print("Initiating vídeo caputre...")

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
    start = time.time()
    period = 10.0 / fps

    

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
    from collections import deque
    # from elasticsearch import Elasticsearch

    # stack to register last 10 emotions (5 seconds?????)
    faceStack = deque(maxlen = 10)

    with open("./Config/application.conf", "r") as confFile:
        conf = json.loads(confFile.read())

    happiness_threshold = conf['happiness_threshold']

    '''    face_id_backend = Elasticsearch(
        conf["face_id_backend"]["hosts"],
        http_auth=(conf["face_id_backend"]["user"], conf["face_id_backend"]["pass"]),
        port=conf["face_id_backend"]["port"],
        scheme=conf["face_id_backend"]["scheme"]
    )
    
    processor = FaceAnalyzer(None, face_id_backend,
                            identify_faces=False,
                            detect_ages=True,
                            detect_emotions=True,
                            detect_genders=True,
                            face_detection_upscales=0)
    '''
    processor = fa.FaceAnalyzer(None, 
                            None,
                            identify_faces=False,
                            detect_ages=False,
                            detect_emotions=True,
                            detect_genders=False,
                            face_detection_upscales=0)
    while True:

        # read new frame
        ret, frame = vcap.read()
        frame = imutils.resize(frame, width=width, height=height)  # resize frame

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

            # print(detections)

            if detections:
                # noinspection PyTypeChecker
                for face in detections["analyzed_faces"]:
                    face_coordinates = face["coordinates"]
                    draw_bounding_box(face_coordinates, frame, (255, 0, 0))

                    if "age" in face and "gender" in face and face["age"] is not None and face["gender"] is not None:
                        age_gender_label = f"{int(face['age'])}, {face['gender']}"
                        draw_label(frame, (face_coordinates["x"], face_coordinates["y"] - 5), age_gender_label)

                    y_offset = 10
                    if "face_id" in face and face["face_id"] is not None:
                        identifier_label = f"{face['face_id']}"
                        draw_label(frame, (face_coordinates["x"] - 50,
                                           face_coordinates["y"] + face_coordinates["h"] + y_offset),
                                   identifier_label, font_scale=0.4, thickness=1)

                    if "emotions" in face and face["emotions"] is not None:
                        y_offset += 10
                        for _label in ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']:
                            emotion_lenght = int(math.ceil(face["emotions"][_label] * 10))
                            if _label == 'happy':
                                if len(faceStack) >= 10:
                                    faceStack.popleft()
                                faceStack.append(emotion_lenght)
                                happiness = np.sum(faceStack)
                                # print(happiness, faceStack)
                                if happiness > happiness_threshold:
                                    happyImage = cv2.imread('./Slides/happy.jpg')
                                    cv2.imshow("happy", happyImage)
                            label_text = _label + ":" + " " * (10 - len(_label))
                            emotions_label = label_text + ("+" * emotion_lenght) + ("-" * (10 - emotion_lenght))
                            coords = (face_coordinates["x"] - 30, 
                                        face_coordinates["y"] + face_coordinates["h"] + y_offset)
                            draw_label(frame, coords, emotions_label, font_scale=0.4, thickness=0)
                            y_offset += 10

            cv2.imshow("Cap: " + str(video_device_id), frame)
            # out.write(frame)

        # if tk gui is being shown, exit by keyword press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
