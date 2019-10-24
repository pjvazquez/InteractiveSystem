# coding=utf-8
import json
import logging
import numpy as np
import requests
import threading

from LogUtil import get_logger

logger = get_logger(__name__)


class NumpyEncoder(json.JSONEncoder):
    # noinspection PyTypeChecker
    def default(self, o):
        if isinstance(o, (
                np.int_, np.intc, np.intp, np.int8, np.int16, np.int32, np.int64, np.uint8, np.uint16,
                np.uint32, np.uint64)):
            return int(o)
        elif isinstance(o, (np.float_, np.float16, np.float32, np.float64)):
            return float(o)
        elif isinstance(o, np.ndarray):
            return o.tolist()

        return json.JSONEncoder.default(self, o)


class Aggregator:
    def __init__(self, agg_time, aggregators, esconf, dont_send=False):
        self.agg_time = agg_time

        self.results_storage = []
        self.aggregators = aggregators

        self.dont_send = dont_send
        if not self.dont_send:
            self.rses = requests.session()
            self.es_url = esconf["es_url"]
            self.es_auth = (esconf["es_user"], esconf["es_pass"])
            self.es_index_name = esconf["es_index_name"]

        # initiate the scheduled sender
        self.f_stop = threading.Event()
        threading.Timer(self.agg_time, self.data_sender, []).start()

    def add(self, data):
        self.results_storage.append(data)

    def data_sender(self):

        # avoid crap between workers
        detections = self.results_storage.copy()
        self.results_storage = []

        hits = []
        for detection in detections:
            (task, payload) = detection
            hits.append({
                **payload,
                "operation": task.operation,
                "app_name": task.app_name,
                "sensor_id": task.sensor_id,
                "task_id": str(task.task_id),
                "time": task.time
            })

        # send hits in a separate thread
        if self.dont_send:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("NOT SENDING STUFF! ndocs: " + str(len(hits)) + ": " + str(hits))
        else:
            if len(hits) > 0:
                threading.Thread(target=self.send_to_es, args=(hits,)).start()
            else:
                logger.debug("No data to be sent this agg step.")

        # reschedule process
        if not self.f_stop.is_set():
            threading.Timer(self.agg_time, self.data_sender, []).start()

    def send_to_es(self, hits):
        logger.info(f"Sending {str(len(hits))} hits to elasticsearch")
        # logger.debug(hits)
        bulk_lines = []
        for hit in hits:
            bulk_lines.append(json.dumps({
                "index": {
                    "_index": self.es_index_name,
                    "_type": "hit"
                }
            }))

            bulk_lines.append(json.dumps(hit, cls=NumpyEncoder))

        payload = "\n".join(bulk_lines) + "\n"

        try:
            res = self.rses.post(self.es_url + "/_bulk",
                                 auth=self.es_auth,
                                 data=payload,
                                 headers={'Content-type': 'Application/Json'})

            if res.status_code != 200:
                logger.critical("Elasticsearch bulk failed!")
                logger.critical(res.text)
                # todo: send this somewhere?
        except requests.exceptions.ConnectionError:
            logger.exception("Error connecting with elasticsearch")
