import logging

def set_logger(name, log_file, level=logging.INFO):
    """Establecer logger para su uso en la app de forma estandarizada"""
    formatter = logging.Formatter('%(asctime)s;%(name)s;%(levelname)s;%(message)s')
    handler = logging.FileHandler(log_file, encoding='utf-8')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    if not logger.handlers:
        logger.addHandler(handler)

    return logger
