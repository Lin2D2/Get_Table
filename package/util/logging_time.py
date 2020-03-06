import logging
import datetime


class LoggingTime:
    def __init__(self, level):
        logging.basicConfig(level=level)

    @staticmethod
    def info(input_stuff):
        return logging.info(":logged at:[" + str(datetime.datetime.now().ctime()) + "]:: " + str(input_stuff))

    @staticmethod
    def debug(input_stuff):
        return logging.debug(":logged at:[" + str(datetime.datetime.now().ctime()) + "]:: " + str(input_stuff))

    @staticmethod
    def warning(input_stuff):
        return logging.warning(":logged at:[" + str(datetime.datetime.now().ctime()) + "]:: " + str(input_stuff))
