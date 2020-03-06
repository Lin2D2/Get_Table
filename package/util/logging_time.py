import logging
import datetime


class LoggingTime:
    def __init__(self, level):
        logging.basicConfig(level=level)

    @staticmethod
    def info(input_stuff, thread=None):
        if not thread:
            return logging.info(":logged at:[" + str(datetime.datetime.now().ctime()) + "]:: " + str(input_stuff))
        else:
            return logging.info(":logged at:[" + str(datetime.datetime.now().ctime())
                                + "]:in \"" + thread + "\":: " + str(input_stuff))

    @staticmethod
    def debug(input_stuff, thread=None):
        if not thread:
            return logging.debug(":logged at:[" + str(datetime.datetime.now().ctime()) + "]:: " + str(input_stuff))
        else:
            return logging.debug(":logged at:[" + str(datetime.datetime.now().ctime())
                                 + "]:in \"" + thread + "\":: " + str(input_stuff))

    @staticmethod
    def warning(input_stuff, thread=None):
        if not thread:
            return logging.warning(":logged at:[" + str(datetime.datetime.now().ctime()) + "]:: " + str(input_stuff))
        else:
            return logging.warning(":logged at:[" + str(datetime.datetime.now().ctime())
                                   + "]:in \"" + thread + "\":: " + str(input_stuff))
