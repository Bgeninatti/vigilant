import datetime
import io
import time

import zmq
from PIL import Image

import tools
from picamera import PiCamera

logger = tools.get_logger('vigilant')

MOVEMENT_THRESHOLD = 10
SENSITIVITY = 20

class Binoculars(object):

    def __init__(self):
        logger.info("Building binoculars")
        self._lens = PiCamera()

    def get_image(self):
        stream = io.BytesIO()
        self._lens.capture(stream, format='bgr')
        stream.seek(0)
        image = Image.open(stream)
        buffer = image.load()
        return image, buffer

class Vigilant(object):

    def __init__(self, binoculars, address='*:5555', blinking_time=.5):
        logger.info("Hiring vigilant")
        self.binoculars = binoculars
        self.address = address
        self.blinking_time = blinking_time
        self.context = None
        self.publisher = None
        self.bell_ringing = False
        self.previous_frame = None
        self.previous_buffer = None

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

    def are_some_movement(self, new_buffer):
        changedPixels = 0
        for x in range(0, 100):
            for y in range(0, 75):
                # Just check green channel as it's the highest quality channel
                pixdiff = abs(self.previous_buffer[x, y][1] - new_buffer[x, y][1])
                if pixdiff > MOVEMENT_THRESHOLD:
                    changedPixels += 1
        return changedPixels > SENSITIVITY

    def take_picture(self, image):
        logger.info("Taking picture")
        time = datetime.now()
        filename = "capture-%04d%02d%02d-%02d%02d%02d.jpg" % (time.year,
                                                              time.month,
                                                              time.day,
                                                              time.hour,
                                                              time.minute,
                                                              time.second)
        image.save(filename)

    def watch(self):
        logger.info("Start watching")
        self._previous_frame, self.previous_buffer = self.binoculars.get_image()
        while not self.bell_ringing:
            logger.info("Seeing in the binoculars.")
            new_frame, new_buffer = self.binoculars.get_image()
            there_is_movement = self.are_some_movement(new_buffer)
            if there_is_movement:
                logger.info("Theres movement!")
                self.take_picture(new_frame)
            self.previous_frame = new_frame
            self.previous_buffer = new_buffer

            logger.info("blinking %ss", self.blinking_time)
            time.sleep(self.blinking_time)
        self._stop_sockets()

