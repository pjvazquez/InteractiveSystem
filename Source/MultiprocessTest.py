# coding=utf-8
import time
import json
import cv2
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


        # initiate detector
        logger.info(" -- Initiating face analyzer models --")

        self.face_analyzer = FaceAnalyzer(None, None, face_detection_upscales=0)

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

if __name__== "__main__":
    with open("./Config/application.conf", "r") as confFile:
        conf = json.loads(confFile.read())

    from captureImage import CaptureImage

    tm = TaskManager(conf)
    tm.load_detector_modules()
    

    captureImage = CaptureImage(0)
    capture = captureImage.OpenVideoCapture()
    
    while True:
        captureImage.ShowVideo(capture)
        task = ImagePredictionTask("faces","x",0,captureImage.frame,1,5)
        tm.enqueue(task)

        if cv2.waitKey(1) == 27:
            break

    captureImage.CloseVideoCapture(capture)