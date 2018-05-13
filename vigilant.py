import io
import time
from datetime import datetime

import numpy as np
import zmq
from PIL import Image

import tools
from picamera import PiCamera

logger = tools.get_logger('vigilant')

MOVEMENT_THRESHOLD = 10
SENSITIVITY = 20
WATCH_RESOLUTION = (360, 240)
SAVE_RESOLUTION = (720, 480)


class Binoculars(object):

    def __init__(self):
        logger.info("Building binoculars")
        self._lens = PiCamera()
        self._lens.rotation = 180
        self._lens.resolution = WATCH_RESOLUTION

    def _get_image(self):
        stream = io.BytesIO()
        self._lens.capture(stream, format='jpeg')
        stream.seek(0)
        image = Image.open(stream)
        return image

    def get_full_image(self):
        self._lens.resolution = SAVE_RESOLUTION
        image = self._get_image()
        self._lens.resolution = WATCH_RESOLUTION
        return image

    def get_green_pixels(self):
        image = self._get_image()
        pixels = np.array(image.reshape(WATCH_RESOLUTION[0],
                                        WATCH_RESOLUTION[1],
                                        3))
        green_pixels = pixels[:, :, 1]
        return green_pixels


class Vigilant(object):

    def __init__(self, binoculars, address='*:5555', blinking_time=.5):
        logger.info("Hiring vigilant")
        self.binoculars = binoculars
        self.address = address
        self.blinking_time = blinking_time
        self.context = None
        self.publisher = None
        self.bell_ringing = False
        self.previous_pixels = None

    def _init_sockets(self):
        self.context = zmq.Context()
        time.sleep(1)
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind('tcp://{}'.format(self.address))
        time.sleep(1)

    def _stop_sockets(self):
        self.publisher.setsockopt(zmq.LINGER, 0)
        self.publisher.close()
        self.context.term()

    def are_some_movement(self):
        actual_pixels = self.binoculars.get_quick_view_image()
        changedPixels = sum(sum((self.previous_pixels - actual_pixels) > MOVEMENT_THRESHOLD))
        self.previous_pixels = actual_pixels
        return changedPixels > SENSITIVITY

    def take_picture(self):
        logger.info("Taking picture")
        image = self.binoculars.get_full_image()
        filename = datetime.now().strftime("capture-%Y%m%d-%H:%M:%S.jpg")
        image.save(filename)

    def watch(self):
        logger.info("Start watching")
        self.previous_pixels = self.binoculars.get_quick_view_image()
        while not self.bell_ringing:
            logger.info("Seeing in the binoculars.")
            if self.are_some_movement():
                logger.info("Theres movement!")
                self.take_picture()
            logger.info("blinking %ss", self.blinking_time)
            time.sleep(self.blinking_time)

