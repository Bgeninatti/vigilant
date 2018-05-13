import io
import time
from datetime import datetime

import numpy as np
import zmq
from PIL import Image

import tools
from picamera import PiCamera

logger = tools.get_logger('vigilant')

MOVEMENT_THRESHOLD = .10
WATCH_RESOLUTION = (90, 60)
SENSITIVITY = .10 * (WATCH_RESOLUTION[0] * WATCH_RESOLUTION[1])
SAVE_RESOLUTION = (720, 480)


class Binoculars(object):

    def __init__(self, watch_resolution=WATCH_RESOLUTION, save_resolution=SAVE_RESOLUTION):
        logger.info("Building binoculars")
        self._lens = PiCamera()
        self._lens.rotation = 180
        self.watch_resolution = watch_resolution
        self.save_resolution = save_resolution
        self._lens.resolution = self.watch_resolution

    def _get_image(self):
        stream = io.BytesIO()
        self._lens.capture(stream, format='jpeg')
        stream.seek(0)
        image = Image.open(stream)
        return image

    def get_full_image(self):
        self._lens.resolution = self.save_resolution
        image = self._get_image()
        self._lens.resolution = self.watch_resolution
        return image

    def get_green_pixels(self):
        image = self._get_image()
        pixels = np.array(image.getdata()).reshape(self.watch_resolution[0],
                                                   self.watch_resolution[1],
                                                   3)
        green_pixels = pixels[:, :, 1]
        return green_pixels


class Vigilant(object):

    def __init__(self,
                 binoculars,
                 movement_threshold=MOVEMENT_THRESHOLD,
                 sensitivity=SENSITIVITY,
                 address='*:5555',
                 blinki6g_time=.5):
        logger.info("Hiring vigilant")
        self.binoculars = binoculars
        self.address = address
        self.blinking_time = blinking_time
        self.movement_threshold = MOVEMENT_THRESHOLD
        self.sensitivity = sensitivity
        self.pixels_sensitivity = self._compute_pixel_sensitivity(sensitivity)
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

    def _compute_pixel_sensitivity(sensitivity):
        return sensitivity * (self.watch_resolution[0]*self.watch_resolution[1])

    def are_some_movement(self):
        actual_pixels = self.binoculars.get_green_pixels()
        relative_difference = (self.previous_pixels - actual_pixels)/self.previous_pixels
        changedPixels = sum(sum(relative_difference > self.movement_threshold))
        self.previous_pixels = actual_pixels
        return changedPixels > self.pixels_sensitivity

    def take_picture(self):
        logger.info("Taking picture")
        image = self.binoculars.get_full_image()
        filename = datetime.now().strftime("capture-%Y%m%d-%H:%M:%S.jpg")
        image.save(filename)

    def watch(self):
        logger.info("Start watching")
        self.previous_pixels = self.binoculars.get_green_pixels()
        while not self.bell_ringing:
            logger.info("Seeing in the binoculars.")
            if self.are_some_movement():
                logger.info("Theres movement!")
                self.take_picture()
            logger.info("blinking %ss", self.blinking_time)
            time.sleep(self.blinking_time)

