
import tools
from vigilant import Vigilant

logger = tools.get_logger('vigilant')


def start_turn():
    logger.info("Starting turn")
    eddy = Vigilant()
    try:
        eddy.watch()
    except KeyboardInterrupt:
        logger.info("RIIIIIIIIINNGGGG...")
        eddy.bell_ringing = True


if __name__ == '__main__':
    start_turn()
