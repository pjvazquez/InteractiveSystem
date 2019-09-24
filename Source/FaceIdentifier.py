# coding=utf-8
import dlib
import numpy as np
import operator
import uuid
# load dlib models
from multiprocessing.dummy import Pool
from typing import Tuple

from FaceIdentifierCacheDriver import CacheDriver

pose_predictor = dlib.shape_predictor("./models/face_detection/shape_predictor_68_face_landmarks.dat")
face_encoder = dlib.face_recognition_model_v1("./models/face_detection/dlib_face_recognition_resnet_model_v1.dat")


def get_best_match(similar_faces, max_encodings_per_face):
    # find the most matched face between closest ones
    found_ids = {}
    for k in similar_faces:
        k_id = k["metadata"]
        try:
            found_ids[k_id] += 1
        except KeyError:
            found_ids[k_id] = 1

    # get the face with the most coincidences
    # TODO: which one is the best option?
    # print(sorted(found_ids.items(), key=operator.itemgetter(1), reverse=True))
    best_match = max(found_ids.items(), key=operator.itemgetter(1))  # (face_id:str, conficence:float)
    print(best_match)
    return best_match[0], float(best_match[1] / max_encodings_per_face)


# non-class function is goodly pickable ¯\_(ツ)_/¯
def process_face_encodings(new_face_encoding, cd, max_encodings_per_face, refresh_after=False):
    similar_faces = cd.retrieve_similar_records(new_face_encoding)

    detected_face: Tuple[str, float] = None
    if len(similar_faces) > 0:
        detected_face = get_best_match(similar_faces, max_encodings_per_face)
        print(detected_face)
        if detected_face[1] < 1:
            cd.insert_record(new_face_encoding, metadata=detected_face[0], refresh_after=refresh_after)
    else:
        print("No similar faces found!")

    # new face detected
    if detected_face is None:
        print("NEW FACE DETECTED!!!!")
        new_id = str(uuid.uuid4())
        detected_face = (new_id, 0.0)
        cd.insert_record(new_face_encoding, metadata=new_id, refresh_after=refresh_after)

    # TODO: remove less relevant hashes for this face!

    return detected_face[0]


def build_face_encodings(aligned_face, num_jitters=1):
    """
    Given an image, return the 128-dimension face encoding for each face in the image.

    :param aligned_face: The image that contains the face
    :param num_jitters: How many times to re-sample the face when calculating encoding. Higher is more accurate
    :return: A list of 128-dimensional face encodings
    """

    # fix dlib's FaceAligner type
    aligned_face = aligned_face.astype('uint8')

    # reformat face locations to match the face_recognition format "top, right, bottom, left"
    face_location = 0, aligned_face.shape[1], aligned_face.shape[0], 0

    _css_to_rect = lambda css: dlib.rectangle(css[3], css[0], css[1], css[2])
    _build_descriptor = lambda face_image, raw_landmark_set: \
        np.array(face_encoder.compute_face_descriptor(face_image, raw_landmark_set, num_jitters))

    # build dlib rect objects from face locations
    face_location = _css_to_rect(face_location)
    # compute face landmarks with the pose predictor
    raw_landmark = pose_predictor(aligned_face, face_location)
    # compute face descriptors for every landmark set
    return _build_descriptor(aligned_face, raw_landmark)


def _indentify_faces(aligned_face, num_jitters, cd, max_encodings_per_face, refresh_after):
    # generate face encodings
    face_encodings = build_face_encodings(aligned_face, num_jitters=num_jitters)
    # build encoding vectors for each face
    face_id = process_face_encodings(face_encodings, cd, max_encodings_per_face, refresh_after=refresh_after)

    return face_id


class FaceIdentifier:
    def __init__(self, es, max_encodings_per_face=5, comparison_tolerance=0.2, num_jilters=1):
        self.max_encodings_per_face = max_encodings_per_face
        self.num_jilters = num_jilters
        self.comparison_tolerance = comparison_tolerance
        self.cd = CacheDriver(es, distance_cutoff=self.comparison_tolerance)
        self.pool = Pool()

    def identify_faces(self, aligned_faces):
        # generate face encoding for every face (multithreaded)
        # TODO: OPTIMIZAME!
        # noinspection PyTypeChecker
        map_args = zip(
            aligned_faces,
            np.repeat(self.num_jilters, len(aligned_faces)),
            np.repeat(self.cd, len(aligned_faces)),
            np.repeat(self.max_encodings_per_face, len(aligned_faces)),
            np.repeat(True, len(aligned_faces))
        )

        # t1 = time.time()
        face_ids = self.pool.starmap(_indentify_faces, map_args)
        # print("faceid time: " + str(time.time() - t1))

        return face_ids

    def index_face(self, aligned_face, face_id, refresh_after=False):
        # generate face encodings
        face_encoding = build_face_encodings(aligned_face, num_jitters=self.num_jilters)
        self.cd.insert_record(face_encoding, metadata=face_id, refresh_after=refresh_after)

    def get_face_id(self, aligned_face_samples, max_dist=0.3):
        print("searching for face_id from %d samples" % len(aligned_face_samples))

        sample_matches = []
        for s in aligned_face_samples:
            matches = self.cd.retrieve_similar_records(build_face_encodings(s))
            sample_matches += matches

        found_ids = {}
        found_ids_dists = {}
        for k in sample_matches:
            k_id = k["metadata"]
            dist = k["dist"]
            try:
                found_ids[k_id] += 1
                found_ids_dists[k_id] += dist
            except KeyError:
                found_ids[k_id] = 1
                found_ids_dists[k_id] = dist

        if len(found_ids) == 0:
            return None

        # promediate distance
        best_match = max(found_ids.items(), key=operator.itemgetter(1))
        best_match = best_match[0], found_ids_dists[best_match[0]] / best_match[1]
        print(best_match)
        return None if best_match[1] > max_dist else best_match[0]
