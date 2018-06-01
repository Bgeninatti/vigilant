import time
import numpy as np
from picamera import PiCamera, streams, array
from vigilant import Watcher


class DetectMotion(array.PiMotionAnalysis):

    def __init__(self, camera):
        super().__init__(camera)
        self.timeout = time.time() + .5

    def analyze(self, a):
        if time.time() > self.timeout:
            a = np.sqrt(
                np.square(a['x'].astype(np.float)) +
                np.square(a['y'].astype(np.float))
            ).clip(0, 255).astype(np.uint8)
            print(sum(a))
            #print(sum(a['x']))
            #print(sum(a['y']))
            print()
            self.timeout = time.time() + .5

if __name__ == '__main__':
    camera = PiCamera()
    try:
        camera.start_recording('/dev/null', format='h264', motion_output=DetectMotion(camera))
        camera.wait_recording(10)
    except KeyboardInterrupt:
        camera.stop_recording()
        print("Chau")
