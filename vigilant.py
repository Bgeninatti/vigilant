import io
import os
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
SENSITIVITY = .30
SAVE_RESOLUTION = (720, 480)
SAVE_FOLDER = '/home/pi/mnt'

class Binoculars(object):

    def __init__(self):
        logger.info("Building binoculars")
        self._lens = PiCamera()
        self._lens.rotation = 180

    def get_image(self):
        stream = io.BytesIO()
        self._lens.capture(stream, format='jpeg')
        stream.seek(0)
        image = Image.open(stream)
        return image

    def record_video(self, time=10):
        filename = datetime.now().strftime("record-%Y%m%d-%H:%M:%S.h264")
        self._lens.start_recording(os.path.join(SAVE_FOLDER, filename))
        self._lens.wait_recording(time)
        self._lens.stop_recording()

    def set_resolution(self, resolution):
        self._lens.resolution = resolution

    def get_resolutio(self):
        return self._lens.resolution

    def get_green_pixels(self):
        image = self.get_image()
        pixels = np.array(image.getdata()).reshape(self._lens.resolution[0],
                                                   self._lens.resolution[1],
                                                   3)
        green_pixels = pixels[:, :, 1]
        return green_pixels


class Vigilant(object):

    def __init__(self,
                 binoculars,
                 movement_threshold=MOVEMENT_THRESHOLD,
                 sensitivity=SENSITIVITY,
                 ip='*',
                 publisher_port=5555,
                 commands_port=5556,
                 blinking_time=0,
                 watch_resolution=WATCH_RESOLUTION,
                 record_resolution=SAVE_RESOLUTION):
        logger.info("Hiring vigilant")
        self.binoculars = binoculars

        self.ip = ip
        self.publisher_port = publisher_port
        self.commands_port = commands_port
        self.context = None
        self.publisher = None
        self.commands = None

        self.blinking_time = blinking_time

        self.watch_resolution = watch_resolution
        self.record_resolution = record_resolution
        self.movement_threshold = movement_threshold
        self.sensitivity = sensitivity
        self.pixels_sensitivity = self.compute_pixel_sensitivity()

        self.bell_ringing = False
        self.previous_pixels = None

        self._init_sockets()

    def _init_sockets(self):
        self.context = zmq.Context()
        time.sleep(1)
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind('tcp://{0}:{1}'.format(self.ip, self.publisher_port))
        time.sleep(1)
        self.commands = self.context.socket(zmq.REP)
        self.commands.bind('tcp://{0}:{1}'.format(self.ip, self.commands_port))
        time.sleep(1)

    def _stop_sockets(self):
        self.publisher.setsockopt(zmq.LINGER, 0)
        self.publisher.close()
        self.commands.setsockopt(zmq.LINGER, 0)
        self.commands.close()
        self.context.term()

    def compute_pixel_sensitivity(self):
        return self.sensitivity * (self.watch_resolution[0]*self.watch_resolution[1])

    def are_some_movement(self):
        actual_pixels = self.binoculars.get_green_pixels()
        pixel_difference = self.previous_pixels - actual_pixels
        changedPixels = sum(sum(pixel_difference > self.movement_threshold * 256))
        self.previous_pixels = actual_pixels
        return changedPixels > self.sensitivity

    def report_movement_state(self):
        movement = self.are_some_movement()
        logger.debug("Reporting movement state")
        self.publisher.send_string('movement\n{0}\n{1}'.format(movement,
                                                               time.time()))

    def take_picture(self, full_resolution=True):
        if full_resolution:
            self.binoculars.set_resolution(self.record_resolution)
        logger.info("Taking picture")
        image = self.binoculars.get_image()
        filename = datetime.now().strftime("capture-%Y%m%d-%H:%M:%S.jpg")
        image.save(os.path.join(SAVE_FOLDER, filename))
        if full_resolution:
            self.binoculars.set_resolution(self.watch_resolution)

    def watch(self):
        logger.info("Start watching")
        self.binoculars.set_resolution(self.watch_resolution)
        self.previous_pixels = self.binoculars.get_green_pixels()
        while not self.bell_ringing:
            logger.info("Seeing in the binoculars.")
            if self.are_some_movement():
                logger.info("Something is moving!")
                self.binoculars.take_picture()
            logger.info("blinking %ss", self.blinking_time)
            time.sleep(self.blinking_time)
        self._stop_sockets()
