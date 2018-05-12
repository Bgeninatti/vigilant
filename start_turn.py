
import tools
from vigilant import Binoculars, Vigilant

logger = tools.get_logger('turn')


def start_turn():
    logger.info("Building binoculars")
    eddys_binoculars = Binoculars()
    logger.info("Calling Eddy")
    eddy = Vigilant(eddys_binoculars)

    try:
        logger.info("Eddy, watch...")
        eddy.watch()
    except KeyboardInterrupt:
        logger.info("RIIIIIIIIINNGGGG...")
        eddy.bell_ringing = True


if __name__ == '__main__':
    start_turn()
