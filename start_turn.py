
import tools
from vigilant import Binoculars, Vigilant

logger = tools.get_logger('turn')


def start_turn():
    logger.info("Starting turn")
    eddys_binoculars = Binoculars()
    eddy = Vigilant(eddys_binoculars)

    try:
        eddy.watch()
    except KeyboardInterrupt:
        logger.info("RIIIIIIIIINNGGGG...")
        eddy.bell_ringing = True


if __name__ == '__main__':
    start_turn()
