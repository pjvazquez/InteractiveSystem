# coding=utf-8
import time
import ray

from Aggregator import Aggregator
from utils import get_logger

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

@ray.remote
class TaskManager():
    def __init__(self, conf ):
        self.conf = conf
        self.task = None
        self.result = None

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
            return task
        except Exception:
            logger.exception("Task failed to be procesed: " + str(task))

    def work(self):
        # this is done here because some features of the tensorflow sessions are not process-safe
        # hence you need to initialize it in the worker process
        self.load_detector_modules()
        logger.info("Modules loaded-----------------------Wait call")
        '''
        logger.info("Here begins the work loop-------------------------------------------")
        
        while True:
            logger.info("inside the while")
            task = self.task
            logger.info("got task from queue")
            if task is None:
                logger.info("task is NONE")
                time.sleep(0.01)
                #break
            else:
                start_time = time.time()
                logger.info(F"Processing task")
                self.process_task(task)
                logger.info(F"Task Result: {task}")
                self.result = task
                logger.info("Task for recover")
        '''
    def start(self):
        logger.info("Starting  workers")
        self.work()

    def set_task(self,task):
        self.task = task

    def get_result(self):
        return self.result

