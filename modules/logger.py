# -*- coding: utf-8 -*-
"""
Logging module for OSINT tool
"""
import logging
import sys
from datetime import datetime
from pathlib import Path

from modules.config import LOGS_DIR


def setup_logger(name: str = "osint", level=logging.INFO) -> logging.Logger:
    """Setup and return a configured logger"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    logger.propagate = False

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console_fmt = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console.setFormatter(console_fmt)
    logger.addHandler(console)

    # File handler
    log_file = LOGS_DIR / f"osint_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    return logger


log = setup_logger()
