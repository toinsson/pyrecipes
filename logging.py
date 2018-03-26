import logging
logger = logging.getLogger()
logging_level = logging.DEBUG

def setup_logging(logger, filename):
    LOG_FORMAT = "[%(module)-15s:%(lineno)5d] %(levelname)5s %(asctime)-5s %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S:%m"
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    handler = logging.StreamHandler()
    handler.setLevel(logging_level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.setLevel(logging_level)


import datetime
datetime_format = "%Y-%m-%d_%H:%M:%S"
def datetime_now(): return datetime.datetime.now().strftime(datetime_format)

