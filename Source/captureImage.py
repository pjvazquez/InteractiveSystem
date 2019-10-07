import cv2
import json
import numpy as np
from datetime import datetime
from functools import wraps
from __init__ import VERSION
from utils import get_logger
from TaskManager import TaskManager, ImagePredictionTask



logger = get_logger(__name__)


# retrieve and parse configuration
with open("./Config/application.conf", "r") as confFile:
    conf = json.loads(confFile.read())



class CaptureImage():
    """
    Capture video from cámera

    Parameters
    ----------
    cameraId : integers
        identifies camera #
    fps: int
        number of frames per second to work with
    """
    def __init__(self, cameraId, fps = 10):
        self.cameraId = cameraId
        self.fps = fps
        self.frame = None

    def OpenVideoCapture(self):
        """
        Open cámera video capture

        Parameters
        ----------
        cameraId : list of integers
            identifies camera #
        fps: int
            number of frames per second to work with
            
        Returns
        -------
        universe : DataFrame
            Selected stocks based on filters
        """
        capture = cv2.VideoCapture(self.cameraId)
        return capture

    def ShowVideo(self, VideoCapture, screenName = 'Video'):
        """
        Show video capture and all windows

        Parameters
        ----------
        VideoCapture : VideopCapture class

        """
        ret, frame = VideoCapture.read()
        self.frame = frame
        cv2.imshow(screenName, frame)

    def CloseVideoCapture(self, VideoCapture):
        """
        Close video capture and all windows

        Parameters
        ----------
        VideoCapture : VideopCapture class

        """
        VideoCapture.release()
        cv2.destroyAllWindows()




if __name__ == "__main__":
    captureImage = CaptureImage(0)
    capture = captureImage.OpenVideoCapture()
    
    while True:
        captureImage.ShowVideo(capture)

        if cv2.waitKey(1) == 27:
            break

    captureImage.CloseVideoCapture(capture)

