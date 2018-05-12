import logging

from vigilant import Binoculars, Vigilant

logger = logging.getLogger('turn')

def start_turn():
    eddys_binoculars = Binoculars()
    eddy = Vigilant(eddys_binoculars)

    try:
        eddy.watch()
    except KeyboardInterrupt:
        eddy.bell_ringing = True


if __name__ == '__main__':
    start_turn()
