# coding=utf-8
import time
from multiprocessing import Process, Queue, Manager

from Aggregator import Aggregator
from LogUtil import get_logger

logger = get_logger(__name__)


class ImagePredictionTask:
    def __init__(self, image, result, time, operation="faces"):
        self.operation = operation
        self.image = image
        self.result = result
        self.time = time
        self.is_gpu_task = operation in ["persons", "faces"]

    def __str__(self):
        return f"Task: operation:{self.operation}, " \
               f"result:{self.result}, " \
               f"time:{self.time}, " \
               f"gputask:{self.is_gpu_task}"


class TaskManager(Process):
    def __init__(self, conf,inqueue, outqueue):
        super(TaskManager, self).__init__()
        self.inqueue = inqueue
        self.outqueue = outqueue
        self.NUMBER_OF_PROCESSES = 1
        self.workers = []
        self.conf = conf

    # noinspection PyAttributeOutsideInit
    def load_detector_modules(self):

        from FaceAnalyzer import FaceAnalyzer

        logger.info(" -- Initiating face analyzer models --")

        self.face_analyzer = FaceAnalyzer(None, 
                            None,
                            identify_faces=False,
                            detect_ages=False,
                            detect_emotions=True,
                            detect_genders=False,
                            face_detection_upscales=0)

        logger.info(" -- ML modules loaded! --")

    def process_task(self, task):

        # noinspection PyBroadException
        try:
            logger.info("Processing frame --------------------------------------")
            self.face_analyzer.process_frame(task)
        except Exception:
            logger.exception("Task failed to be procesed: " + str(task))

    def work(self, worker_id):
        # this is done here because some features of the tensorflow sessions are not process-safe
        # hence you need to initialize it in the worker process
        self.load_detector_modules()
        
        logger.info("Here begins the work loop-------------------------------------------")
        while True:
            logger.debug("inside the while")
            task = self.inqueue.get()
            logger.debug("got task from queue")
            if task is None:
                logger.info("task is NONE")
                time.sleep(0.01)
                break
            start_time = time.time()
            logger.debug(F"Worker {worker_id} consuming task: {task.operation}")
            self.process_task(task)
            logger.debug(F"Task Result: {task}")
            logger.debug(F"Worker {worker_id} is done with task {task.operation}"
                        F"in {time.time() - start_time} seconds. "
                        F"{self.inqueue.qsize()}:{self.outqueue.qsize()} IN:OUT queue status")
            self.outqueue.put(task, True, 0.5)
            logger.debug("Task inserted in OUT QUEUE")
        self.inqueue.put(None)

    def start(self):
        logger.info("Starting %d workers" % self.NUMBER_OF_PROCESSES)

        self.workers = [Process(target=self.work, args=(i,)) for i in range(self.NUMBER_OF_PROCESSES)]
        for w in self.workers:
            w.start()

    def stop(self):
        self.inqueue.put(None)
        self.outqueue.put(None)
        for i in range(self.NUMBER_OF_PROCESSES):
            self.workers[i].join()
        self.inqueue.close()
        self.outqueue.close()

    def enqueue(self, job_payload):
        self.inqueue.put(job_payload)

    def dequeue(self):
        # is it needed
        # do I need a function to get last out element?
        # In MAC OS qsize() rises a Non Implemented Error
        try:
            if self.outqueue.qsize() == 0:
                return None
            else:
                detections = self.outqueue.get()
                logger.debug(F"Task result from queue: {detections}")
                return detections
        except NotImplementedError:
            detections = self.outqueue.get()
            logger.debug(F"Task result from queue: {detections}")
            return detections
