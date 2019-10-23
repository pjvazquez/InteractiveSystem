from threading import Thread
import cv2

class VideoGet:
    """
    Class that continuously gets frames from a VideoCapture object
    with a dedicated thread.
    """

    def __init__(self, src=0, cameraRes=(640,480)):
        # cameraRes is w:1920, h:1080 for linux cam
        self.stream = cv2.VideoCapture(src)
        # set device parameters
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, cameraRes[0])
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, cameraRes[1])
        self.stream.set(cv2.CAP_PROP_FPS, 60)

        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):    
        Thread(target=self.get, args=()).start()
        return self

    def get(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = self.stream.read()

    def stop(self):
        self.stopped = True