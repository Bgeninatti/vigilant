import io
import os
import time
from datetime import datetime
from threading import Event

import numpy as np
import zmq
from PIL import Image

import tools
from picamera import PiCamera, PiCameraCircularIO, array

logger = tools.get_logger('vigilant')

RECORD_RESOLUTION = (1920, 1080)
MOTION_RESOLUTION = (640, 480)
SAVE_FOLDER = '/home/pi/mnt'

CV_THRESHOLD = .9
PRESECONDS = 3
ANALYSE_PERIOD = .5
MACROBLOCK_THRESHOLD = 60
MACROBLOCK_COUNT_FOR_MOTON = 10

class Watcher(array.PiMotionAnalysis):

    def  __init__(self, camera, motion_event):
        super().__init__(camera)
        self.are_some_movement = motion_event
        self.kernel = None
        self._kernel_square = 0
        self.next_analyse_on = time.time() + ANALYSE_PERIOD

    def compute_convolution(self, imagen):
        numerador = sum(sum(imagen * self.kernel))
        pre_denom = sum(sum(self.kernel * self.kernel))
        cv = numerador / np.sqrt(numerador * pre_denom)
        return cv

    def update_kernel(self, frame):
        self.kernel = frame
        self._kernel_square = sum(sum(frame * frame))

    def analyze(self, macroblock):
        if time.time() > self.next_analyse_on:
            a = np.sqrt(
                np.square(macroblock['x'].astype(np.float)) +
                np.square(macroblock['y'].astype(np.float))
                ).clip(0, 255).astype(np.uint8)
            if (a > MACROBLOCK_THRESHOLD).sum() > MACROBLOCK_COUNT_FOR_MOTON:
                self.are_some_movement.set()
            else:
                self.are_some_movement.clear()
            self.next_analyse_on = time.time() + ANALYSE_PERIOD


class Binoculars(object):

    def __init__(self, are_some_movement):
        logger.info("Building binoculars")
        self._lens = PiCamera()
        self._lens.rotation = 180
        self.buffer = PiCameraCircularIO(self._lens, seconds=PRESECONDS)
        self.watcher = Watcher(self._lens, are_some_movement)
        self.is_recording = False

    def start_watching(self):
        self._lens.start_recording(self.buffer,
                                   format='h264',
                                   resize=RECORD_RESOLUTION,
                                   splitter_port=1)
        self._lens.start_recording('/dev/null',
                                   format='h264',
                                   resize=MOTION_RESOLUTION,
                                   splitter_port=2,
                                   motion_output=self.watcher)

    def start_recording(self, filename):
        self.is_recording = True
        self._lens.split_recording(filename, splitter_port=1)

    def stop_recording(self):
        self.is_recording = False
        self._lens.split_recording(self.buffer, splitter_port=1)

    def save_buffer(self, filename):
        self.buffer.copy_to(filename)

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

    def take_picture(self):
        logger.info("Taking picture")
        i.get_image()
        filename = datetime.now().strftime("capture-%Y%m%d-%H:%M:%S.jpg")
        image.save(os.path.join(SAVE_FOLDER, filename))


class Vigilant(object):

    def __init__(self):
        logger.info("Hiring vigilant")
        self.are_some_movement = Event()
        self.binoculars = Binoculars(self.are_some_movement)
        self.bell_ringing = False

    def get_or_create_folder(self):
        folder = datetime.now().strftime("%Y%m%d")
        if not os.path.exists(folder):
            os.makedirs(folder)
        return folder

    def get_event_filename(self):
        folder = self.get_or_create_folder()
        events_number = len(os.listdir(folder))
        filename = datetime.now().strftime("event-{}-%Y%m%d").format(events_number +  1)
        filename_with_path = os.path.join(folder, filename)
        return filename_with_path

    def watch(self):
        logger.info("Start watching")
        self.binoculars.start_watching()
        while not self.bell_ringing:
            if self.are_some_movement.is_set() and not self.binoculars.is_recording:
                logger.info("Something is moving!")
                filename = self.get_event_filename()
                self.binoculars.start_recording(filename)
            elif not self.are_some_movement.is_set() and self.binoculars.is_recording:
                self.binoculars.stop_recording()
