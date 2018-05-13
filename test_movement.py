import time
from vigilant import Vigilant, Binoculars


def init_vigilant():
    binoculars = Binoculars()
    vigilant = Vigilant(binoculars)
    vigilant.previous_pixels = vigilant.binoculars.get_green_pixels()
    return vigilant

vigilant = init_vigilant()
while 1:
    start = time.time()
    print(vigilant.are_some_movement(), time.time())
