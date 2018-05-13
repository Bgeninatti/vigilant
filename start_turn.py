
import tools
from vigilant import Binoculars, Vigilant

logger = tools.get_logger('turn')

def call_eddy():
    eddys_binoculars = Binoculars()
    eddy = Vigilant(eddys_binoculars)
    return eddy

def start_turn():
    logger.info("Starting turn")
    eddy = call_eddy()

    try:
        eddy.watch()
    except KeyboardInterrupt:
        logger.info("RIIIIIIIIINNGGGG...")
        eddy.bell_ringing = True


if __name__ == '__main__':
    start_turn()
