# coding=utf-8
import time

import cv2
import dlib
import numpy as np
from imutils.face_utils import FaceAligner
import imutils

from threading import Thread

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
    def __init__(self,
                frame=None,
                aggregator=None, 
                face_cache_backend=None,
                identify_faces=False,
                detect_genders=False,
                detect_ages=False,
                detect_emotions=True,
                face_detection_upscales=0):

        self.frame = frame
        self.stopped = False

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

    def analyze_frame(self):
        """
        Performs analysis over frame
        Parameters
        ----------
        rgb_frame : captured frame
        Returns
        -------
        analyze_faces : function
        """
        detected_faces, aligned_faces = self.face_detector.detect_faces(self.frame, self.face_detection_upscales)
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



    def start(self):
        print("STARTED FRAME ANALYZER-----------------------------------")
        self.processor = FaceAnalyzer(None, 
                                None,
                                identify_faces=False,
                                detect_ages=False,
                                detect_emotions=True,
                                detect_genders=False,
                                face_detection_upscales=0)
        Thread(target=self.analyze, args=()).start()

    def analyze(self):
        while not self.stopped:
            if self.frame is not None:
                print("TO------- ANALYZE FRAME-----------------------------------")

                try:
                    self.detections = self.processor.analyze_frame(self.frame)
                except Exception:
                    traceback.print_exc()
                    continue

    def stop(self):
        self.stopped = True