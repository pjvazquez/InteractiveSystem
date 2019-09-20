# coding=utf-8
import time
from multiprocessing import Process, Queue

from Aggregator import Aggregator
from utils import get_logger

logger = get_logger(__name__)


class ImagePredictionTask:
    def __init__(self, operation, app_name, sensor_id, image, task_id, time):
        self.operation = operation
        self.app_name = app_name
        self.sensor_id = sensor_id
        self.image = image
        self.task_id = task_id
        self.time = time
        self.is_gpu_task = operation in ["persons", "faces"]

    def __str__(self):
        return f"Task: operation:{self.operation}, " \
               f"sensorId:{self.sensor_id}, " \
               f"app_name:{self.app_name}, " \
               f"task_id:{self.task_id}, " \
               f"time:{self.time}, " \
               f"gputask:{self.is_gpu_task}"


class TaskManager:
    def __init__(self, conf):
        self.queue = Queue()
        self.NUMBER_OF_PROCESSES = 1
        self.workers = []
        self.conf = conf

    # noinspection PyAttributeOutsideInit
    def load_detector_modules(self):

        from FaceAnalyzer import FaceAnalyzer
        from MovementDetector import MovementDetectorManager
        from ObjectDetector import ObjectDetector

        # initiate aggregator
        agg_time = self.conf["aggregation_size"]
        aggregators = {
            "face_analyzer": FaceAnalyzer,
            "movement_detector": MovementDetectorManager,
            "objects": ObjectDetector
        }
        aggregator = Aggregator(agg_time, 
                                aggregators, 
                                self.conf["es_conf"], 
                                dont_send=self.conf["debug_mode"])

        # initiate detectors
        logger.info(" -- Initiating movement detector --")
        self.movement_detector = MovementDetectorManager(aggregator,
                                                         expected_output_dims=(128, 128),
                                                         min_thresh=30,
                                                         min_detection_size=15,
                                                         max_detection_size=250,
                                                         acumulation=1, )

        logger.info(" -- Initiating face analyzer models --")
        # Uses elasticsearch database
        from elasticsearch import Elasticsearch
        face_id_backend = Elasticsearch(
            self.conf["face_id_backend"]["hosts"],
            http_auth=(self.conf["face_id_backend"]["user"], self.conf["face_id_backend"]["pass"]),
            port=self.conf["face_id_backend"]["port"],
            scheme=self.conf["face_id_backend"]["scheme"]
        )
        self.face_analyzer = FaceAnalyzer(aggregator, face_id_backend, face_detection_upscales=0)
        logger.info(" -- Initiating object detector models --")
        # TODO: parametrize this
        self.object_detector = ObjectDetector(aggregator, quality="normal", min_probability=20)
        logger.info(" -- ML modules loaded! --")

    def process_task(self, task):

        # noinspection PyBroadException
        try:
            if task.operation == "persons":
                self.object_detector.detect(task)
            elif task.operation == "movements":
                self.movement_detector.process_frame(task)
            elif task.operation == "faces":
                self.face_analyzer.process_frame(task)
            else:
                logger.error("NOT IMPLEMENTED OPERATION")
        except Exception:
            logger.exception("Task failed to be procesed: " + str(task))

    def work(self, worker_id):
        # this is done here because some features of the tensorflow sessions are not process-safe
        # hence you need to initialize it in the worker process
        self.load_detector_modules()

        while True:
            task = self.queue.get()
            if task is None:
                time.sleep(0.01)
                break

            start_time = time.time()
            logger.info(F"Worker {worker_id} consuming task {task.operation}:{task.task_id} from {task.sensor_id}")
            self.process_task(task)
            logger.info(F"Worker {worker_id} is done with task {task.operation}:{task.task_id} from {task.sensor_id} "
                        F"in {time.time() - start_time} seconds. "
                        F"{self.queue.qsize()} remaining tasks to consume")
        self.queue.put(None)

    def start(self):
        logger.info("Starting %d workers" % self.NUMBER_OF_PROCESSES)

        self.workers = [Process(target=self.work, args=(i,)) for i in range(self.NUMBER_OF_PROCESSES)]
        for w in self.workers:
            w.start()

    def stop(self):
        self.queue.put(None)
        for i in range(self.NUMBER_OF_PROCESSES):
            self.workers[i].join()
        self.queue.close()

    def enqueue(self, job_payload):
        self.queue.put(job_payload)
