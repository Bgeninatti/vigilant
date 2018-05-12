import logging

from vigilant import Binoculars, Vigilant

logger = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger.setFormatter(formatter)


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
