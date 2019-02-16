import logging
import syslog
from logging import StreamHandler
from logging.handlers import SysLogHandler
from ldapauthkeys.config import *
import sys

PROGRAM_NAME = 'openssh-ldap-authkeys'

def get_logger(name='main'):
    """
    Get a logging.Logger() instance suitable for writing log messages from the
    program.
    """
    config = load_config()
    
    name = '%s.%s' % (PROGRAM_NAME, name)
    
    logger = logging.Logger(name)
    
    formatter = logging.Formatter(name + '[%(process)d] %(levelname)s: %(message)s')
    
    handler = SysLogHandler(facility=syslog.LOG_AUTH)
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    if config['logging']['to_stderr']:
        handler = StreamHandler(sys.stderr)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger