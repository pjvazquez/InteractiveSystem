from threading import Thread
import numpy as np
import cv2

class VideoShow:
    """
    Class that continuously shows a frame using a dedicated thread.
    """
    def __init__(self, frame=None):
        self.frame = frame
        self.stopped = False

    def start(self):
        self.show()
        return self

    def show(self):
        cv2.namedWindow("Video", cv2.WND_PROP_FULLSCREEN)
        cv2.moveWindow("Video",3000,0)
        cv2.setWindowProperty("Video",cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
        '''
        while not self.stopped:
            cv2.imshow("Video", self.frame)
            if cv2.waitKey(1) == ord("q"):
                self.stopped = True
        '''
    def stop(self):
        self.stopped = True