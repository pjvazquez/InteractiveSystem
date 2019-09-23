# coding=utf-8
import time

import cv2
import dlib
import numpy as np
from imutils.face_utils import FaceAligner
import imutils

from utils import get_logger

logger = get_logger(__name__)


class FaceDetectorDlib:

    def __init__(self, desired_face_width=200):
        self.detector = dlib.get_frontal_face_detector()
        # TODO: allow less landmarks: https://github.com/davisking/dlib-models
        predictor = dlib.shape_predictor("./Models/face_detection/shape_predictor_68_face_landmarks.dat")
        self.fa = FaceAligner(predictor, desiredFaceWidth=desired_face_width)
        self.desired_face_width = desired_face_width

    def detect_faces(self, frame, upscalings=0):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # detect faces using dlib detector
        detected = self.detector(frame, upscalings)
        faces = np.empty((len(detected), self.desired_face_width, self.desired_face_width, 3))

        detections = []
        for i, d in enumerate(detected):
            # TODO: allow offset margins to be applied here!
            faces[i, :, :, :] = self.fa.align(frame, gray, detected[i])
            # faces[i, :, :, :] =  detected[i]

            # debug stuff
            # cv2.imshow("DEBUG FACE ALIGNMENT " + str(i), faces[i, :, :, :].astype('uint8'))

            face_coordinates = d.left(), d.top(), d.width(), d.height()
            detections.append(face_coordinates)

        return detections, faces


class FaceAnalyzer:
    def __init__(self, aggregator, 
                face_cache_backend,
                identify_faces=False,
                detect_genders=False,
                detect_ages=False,
                detect_emotions=True,
                face_detection_upscales=0):

        # what does Aggregator makes?
        # seems it generates packages for sending to the web server
        # do not use it
        # self.aggregator = aggregator
        self.face_detection_upscales = face_detection_upscales

        self.face_detector = FaceDetectorDlib()

        if detect_genders or detect_ages:
            from AgeGenderDetector import AgeGenderDetector
            self.age_gender_detector = AgeGenderDetector()
        else:
            self.age_gender_detector = None

        if detect_emotions:
            # This is the only detector I'm going to use by the moment
            from EmotionDetector import EmotionDetector
            self.emotion_detector = EmotionDetector()
        else:
            self.emotion_detector = None

        if identify_faces:
            from FaceIdentifier import FaceIdentifier
            self.face_identifier = FaceIdentifier(face_cache_backend,
                                                  max_encodings_per_face=5,
                                                  num_jilters=0,
                                                  comparison_tolerance=0.15)
        else:
            self.face_identifier = None

    def analyze_frame(self, rgb_frame):
        """
        Performs analysis over frame
        Parameters
        ----------
        rgb_frame : captured frame
        Returns
        -------
        analyze_faces : function
        """
        detected_faces, aligned_faces = self.face_detector.detect_faces(rgb_frame, self.face_detection_upscales)
        return self.analyze_faces(detected_faces, aligned_faces)

    def analyze_faces(self, detected_faces, aligned_faces):
        """
        Performs analysis over faces
        Parameters
        ----------
        detected_faces : list of detected faces
        aligned_faces : list of aligned faces
        Returns
        -------
        analyze_faces : function
        """
        # speed up the thing if there are no faces
        if len(detected_faces) == 0:
            return {"frontal_visitors": 0, "detected_males": 0, "detected_females": 0, "analyzed_faces": []}

        # run detection models
        ages_genders = self.age_gender_detector.analyze_faces(aligned_faces) \
            if self.age_gender_detector else [{}] * len(detected_faces)  # ಠ_ಠ
        emotions = self.emotion_detector.analyze_faces(aligned_faces) if self.emotion_detector else None
        identifiers = self.face_identifier.identify_faces(aligned_faces) if self.face_identifier else None

        # compose results
        n_males = len([1 for ag in ages_genders if ag["gender"] == "M"]) if self.age_gender_detector else 0
        n_females = len(detected_faces) - n_males if self.age_gender_detector else 0

        return {
            "frontal_visitors": len(detected_faces),
            "detected_males": n_males,
            "detected_females": n_females,
            "analyzed_faces": [
                {
                    **ages_genders[i],
                    "face_id": identifiers[i] if self.face_identifier else None,
                    "emotions": emotions[i] if self.emotion_detector else None,
                    "coordinates": {
                        "x": detected_faces[i][0],
                        "y": detected_faces[i][1],
                        "h": detected_faces[i][2],
                        "w": detected_faces[i][3],
                    }
                }
                for i in range(0, len(detected_faces))
            ]
        }

    def process_frame(self, task):
        results = self.analyze_frame(task.image)
        if self.aggregator:
            self.aggregator.add((task, results))


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
    processor = FaceAnalyzer(None, 
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
