# coding=utf-8
import tensorflow as tf
# from imutils import resize

import inception_resnet_v1
from utils import get_logger

logger = get_logger(__name__)


class AgeGenderDetector:
    def __init__(self):
        # load model and weights
        self.img_size = 160
        self.sess, self.age, self.gender, self.train_mode, self.images_pl = \
            AgeGenderDetector.load_network("./Models/age_gender")

    def analyze_faces(self, faces):

        # _faces = [resize(f, width=self.img_size, height=self.img_size) for f in faces]
        _faces = [f for f in faces]

        # predict ages and genders of the detected faces
        predicted_ages, predicted_genders = [], []
        if len(_faces) > 0:
            predicted_ages, predicted_genders = self.sess.run(
                [self.age, self.gender],
                feed_dict={self.images_pl: _faces, self.train_mode: False}
            )

        return [
            {
                "age": round(predicted_ages[k], 1),
                "gender": "F" if predicted_genders[k] == 0 else "M"
            } for k in range(0, len(_faces))
        ]

    @staticmethod
    def load_network(model_path):

        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True

        sess = tf.Session(config=config)
        images_pl = tf.placeholder(tf.float32, shape=[None, 160, 160, 3], name='input_image')
        images_norm = tf.map_fn(lambda frame: tf.image.per_image_standardization(frame), images_pl)
        train_mode = tf.placeholder(tf.bool)
        age_logits, gender_logits, _ = inception_resnet_v1.inference(images_norm, keep_probability=0.8,
                                                                     phase_train=train_mode,
                                                                     weight_decay=1e-5)
        gender = tf.argmax(tf.nn.softmax(gender_logits), 1)
        age_ = tf.cast(tf.constant([i for i in range(0, 101)]), tf.float32)
        age = tf.reduce_sum(tf.multiply(tf.nn.softmax(age_logits), age_), axis=1)
        init_op = tf.group(tf.global_variables_initializer(), tf.local_variables_initializer())
        sess.run(init_op)
        saver = tf.train.Saver()
        ckpt = tf.train.get_checkpoint_state(model_path)

        if ckpt and ckpt.model_checkpoint_path:
            saver.restore(sess, ckpt.model_checkpoint_path)
            logger.info("Restored model!")
        else:
            logger.critical("Age and Gender model not restored!")
        return sess, age, gender, train_mode, images_pl
