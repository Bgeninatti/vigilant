import datetime
import os
import time

from picamera import PiCamera

RESOLUTION = (2592, 1944)
PHOTO_INTERVAL = 30
PHOTOS_DIRECTORY = '/home/pi/mnt'
SPY_PERIOD = 5 * 3600
PHOTO_FORMAT = 'jpeg'

class Spy(object):

    def __init__(self):
        self.camera = PiCamera()
        self.resolution = RESOLUTION
        self.spy_until = 0

    def spying(self):
        self.spy_until = time.time() + SPY_PERIOD
        while time.time() < self.spy_until:
            filename = self._get_filename()
            self.camera.capture(filename, format=PHOTO_FORMAT)
            time.sleep(PHOTO_INTERVAL)

    def _get_filename(self):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        filename = os.path.join(PHOTOS_DIRECTORY, 'img_{}.jpg'.format(now))
        return filename
