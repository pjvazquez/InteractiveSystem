# coding=utf-8
import cv2
import keras
import numpy as np
import tensorflow as tf


class EmotionDetector:
    def __init__(self):
        self.emotion_labels = {0: 'angry', 1: 'disgust', 2: 'fear', 3: 'happy', 4: 'sad', 5: 'surprise', 6: 'neutral'}

        # load models
        emotion_model_path = './Models/emotions/fer2013_big_XCEPTION.54-0.66.hdf5'
        self.emotion_classifier = keras.models.load_model(emotion_model_path, compile=False)
        self.graph = tf.get_default_graph()

        # getting input model shapes for inference
        self.emotion_target_size = self.emotion_classifier.input_shape[1:3]

        # starting lists for calculating modes
        self.emotion_window = []

    @staticmethod
    def apply_offsets(face_coordinates):
        x, y, width, height = face_coordinates
        return x, x + width, y, y + height

    @staticmethod
    def preprocess_input(x):
        x: object = x.astype('float32')
        x /= 255.0
        x -= 0.5
        x *= 2.0

        return x

    def analyze_faces(self, faces):

        predictions = []
        for face in faces:
            # adapt face format to
            gray_face = cv2.resize(face, self.emotion_target_size)
            gray_face = EmotionDetector.preprocess_input(gray_face)
            gray_face = cv2.cvtColor(gray_face, cv2.COLOR_RGB2GRAY)
            # noinspection PyTypeChecker
            gray_face = np.expand_dims(gray_face, 0)
            gray_face = np.expand_dims(gray_face, -1)

            # run images through the model
            with self.graph.as_default():
                emotion_prediction = self.emotion_classifier.predict(gray_face)

            predictions.append(emotion_prediction)

        results = []
        for emotion_predictions in predictions:
            for emotion_prediction in emotion_predictions:
                results.append({
                    self.emotion_labels[k]: round(emotion_prediction[k], 3)
                    for k in self.emotion_labels
                })

        return results
