import base64
import io
import time

import zmq

import tools
from picamera import PiCamera

logger = tools.get_logger()

class Binoculars(object):

    def __init__(self):
        self._lens = PiCamera()

    def get_image(self):
        stream = io.BytesIO()
        self._lens.capture(stream, format='bgr')
        b64_image = base64.b64encode(stream.getvalue())
        return b64_image

class Vigilant(object):

    def __init__(self, binoculars, address='*:5555', blinking_time=.5):
        self.binoculars = binoculars
        self.address = address
        self.blinking_time = blinking_time
        self.context = None
        self.publisher = None
        self.bell_ringing = False

        self._init_sockets()

    def _init_sockets(self):
        self.context = zmq.Context()
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind('tcp://{}'.format(self.address))

    def _stop_sockets(self):
        self.publisher.setsockopt(zmq.LINGER, 0)
        self.publisher.close()
        self.context.term()

    def watch(self):
        while not self.bell_ringing:
            logger.info("Seeing in the binoculars.")
            image = self.binoculars.get_image()
            logger.info("Sending %s bytes", len(image))
            self.publisher.send(image)
            logger.info("blinking %ss", self.blinking_time)
            time.sleep(self.blinking_time)
        self._stop_sockets()

