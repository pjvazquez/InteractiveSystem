# coding=utf-8
import elasticsearch
import numpy as np
from datetime import datetime
from elasticsearch import Elasticsearch
from operator import itemgetter


def get_words(array, k, N):
    """Gets N words of length k from an array.

    Words may overlap.

    For example, say your image signature is [0, 1, 2, 0, -1, -2, 0, 1] and
    k=3 and N=4. That means we want 4 words of length 3.  For this signature,
    that gives us:

    [0, 1, 2]
    [2, 0, -1]
    [-1, -2, 0]
    [0, 1]

    Args:
        array (numpy.ndarray): array to split into words
        k (int): word length
        N (int): number of words

    Returns:
        an array with N rows of length k

    """
    # generate starting positions of each word
    word_positions = np.linspace(0, array.shape[0],
                                 N, endpoint=False).astype('int')

    # check that inputs make sense
    if k > array.shape[0]:
        raise ValueError('Word length cannot be longer than array length')
    if word_positions.shape[0] > array.shape[0]:
        raise ValueError('Number of words cannot be more than array length')

    # create empty words array
    words = np.zeros((N, k)).astype('int8')

    for i, pos in enumerate(word_positions):
        if pos + k <= array.shape[0]:
            words[i] = array[pos:pos + k]
        else:
            temp = array[pos:].copy()
            temp.resize(k)
            words[i] = temp

    return words


def words_to_int(word_array):
    """Converts a simplified word to an integer

    Encodes a k-byte word to int (as those returned by max_contrast).
    First digit is least significant.

    Returns dot(word + 1, [1, 3, 9, 27 ...] ) for each word in word_array

    e.g.:
    [ -1, -1, -1] -> 0
    [ 0,   0,  0] -> 13
    [ 0,   1,  0] -> 16

    Args:
        word_array (numpy.ndarray): N x k array

    Returns:
        an array of integers of length N (the integer word encodings)

    """
    width = word_array.shape[1]

    # Three states (-1, 0, 1)
    coding_vector = 3 ** np.arange(width)

    # The 'plus one' here makes all digits positive, so that the
    # integer represntation is strictly non-negative and unique
    return np.dot(word_array + 1, coding_vector)


def max_contrast(array):
    """Sets all positive values to one and all negative values to -1.

    Needed for first pass lookup on word table.

    Args:
        array (numpy.ndarray): target array
    """
    array[array > 0] = 1
    array[array < 0] = -1

    return None


def normalized_distance(_target_array, _vec, nan_value=1.0):
    """Compute normalized distance to many points.

    Computes || vec - b || / ( ||vec|| + ||b||) for every b in target_array

    Args:
        _target_array (numpy.ndarray): N x m array
        _vec (numpy.ndarray): array of size m
        nan_value (Optional[float]): value to replace 0.0/0.0 = nan with
            (default 1.0, to take those featureless images out of contention)

    Returns:
        the normalized distance (float)
    """
    target_array = _target_array.astype(float)
    vec = _vec.astype(float)
    topvec = np.linalg.norm(vec - target_array, axis=1)
    norm1 = np.linalg.norm(vec, axis=0)
    norm2 = np.linalg.norm(target_array, axis=1)
    finvec = topvec / (norm1 + norm2)
    finvec[np.isnan(finvec)] = nan_value

    return finvec


class SignatureES:
    """Elasticsearch driver for image-match

    """

    def __init__(self, es: Elasticsearch, index='face_signatures', doc_type='doc', timeout='10s', distance_cutoff=0.4,
                 size=100, *args, **kwargs):
        """Extra setup for Elasticsearch

        Args:
            es (elasticsearch): an instance of the elasticsearch python driver
            index (Optional[string]): a name for the Elasticsearch index (default 'images')
            doc_type (Optional[string]): a name for the document time (default 'image')
            timeout (Optional[int]): how long to wait on an Elasticsearch query, in seconds (default 10)
            size (Optional[int]): maximum number of Elasticsearch results (default 100)
            *args (Optional): Variable length argument list to pass to base constructor
            **kwargs (Optional): Arbitrary keyword arguments to pass to base constructor
        """
        self.es = es
        self.index = index
        self.doc_type = doc_type
        self.timeout = timeout
        self.size = size
        self.distance_cutoff = distance_cutoff

        super(SignatureES, self).__init__(*args, **kwargs)

    def search_single_record(self, rec, pre_filter=None):
        signature = rec.pop('signature')
        if 'metadata' in rec:
            rec.pop('metadata')

        # build the 'should' list
        should = [{'term': {word: rec[word]}} for word in rec]
        body = {
            'query': {
                'bool': {'should': should}
            },
            '_source': {'excludes': ['simple_word_*']}
        }

        if pre_filter is not None:
            body['query']['bool']['filter'] = pre_filter

        res = self.es.search(index=self.index,
                             doc_type=self.doc_type,
                             body=body,
                             size=self.size,
                             timeout=self.timeout)['hits']['hits']

        sigs = np.array([x['_source']['signature'] for x in res])

        if sigs.size == 0:
            return []

        dists = normalized_distance(sigs, np.array(signature))

        formatted_res = [
            {
                'id': x['_id'],
                'score': x['_score'],
                'signature': x['_source'].get('signature'),
                'metadata': x['_source'].get('metadata')
            }
            for x in res
        ]

        for i, row in enumerate(formatted_res):
            row['dist'] = dists[i]
        formatted_res = filter(lambda y: y['dist'] < self.distance_cutoff, formatted_res)

        return formatted_res

    def insert_single_record(self, rec, refresh_after=False):
        rec['timestamp'] = datetime.now()
        self.es.index(index=self.index, doc_type=self.doc_type, body=rec, refresh="true" if refresh_after else "false")


class CacheDriver:
    def __init__(self, es, k=1, n=128, distance_cutoff=0.5):
        self.k = k
        self.n = n

        self.signature_db = SignatureES(es, distance_cutoff=distance_cutoff)

    def build_record(self, signature, metadata=None):
        words = get_words(signature, self.k, self.n)
        max_contrast(words)

        words = words_to_int(words)

        record = dict()
        record['signature'] = signature.tolist()
        record['metadata'] = metadata

        for i in range(self.n):
            record[''.join(['simple_word_', str(i)])] = words[i].tolist()

        return record

    def insert_record(self, signature, metadata, refresh_after=False):
        record = self.build_record(signature, metadata=metadata)
        self.signature_db.insert_single_record(record, refresh_after=refresh_after)

    def retrieve_similar_records(self, signature):
        record = self.build_record(signature)
        try:
            founds = self.signature_db.search_single_record(record)
            return sorted(founds, key=itemgetter('dist'))
        except elasticsearch.exceptions.NotFoundError:
            return []


if __name__ == "__main__":
    cd = CacheDriver(Elasticsearch(), distance_cutoff=0.5)

    signature = np.random.rand(128)
    cd.insert_record(signature, "some random id")
    founds = cd.retrieve_similar_records(signature)

    print(founds)
