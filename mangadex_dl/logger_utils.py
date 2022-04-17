"""Logging utils for mangdex_dl"""
import logging

import tqdm


class TqdmLoggingHandler(logging.Handler):
    """
    Handles logging for tqdm
    """

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except Exception:
            self.handleError(record)
