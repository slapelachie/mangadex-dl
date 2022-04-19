"""Classes and functions for reporting"""
import logging
import threading
from time import time, sleep

import requests
import tqdm

from mangadex_dl.typehints import ReportInfo
from mangadex_dl.logger_utils import TqdmLoggingHandler

logger = logging.getLogger(__name__)
logger.addHandler(TqdmLoggingHandler())
logger.propagate = False


class MangadexReporter:
    """A report handler for mangadex, called whenever an image is downloaded"""

    def __init__(self):
        self._reports = []
        self._report_total = 0
        self._reporting = False

    def _report(self):
        self._reporting = True
        with tqdm.tqdm(
            total=len(self._reports),
            ascii=True,
            desc="Reports",
            leave=False,
            position=2,
        ) as tbar:
            while len(self._reports) > 0:
                report = self._reports[0]

                if tbar.total != self._report_total:
                    tbar.total = self._report_total
                    tbar.refresh()

                if "uploads.mangadex.org" in report.get("url"):
                    logger.debug(
                        "Endpoint is not from mangadex.network, not reporting..."
                    )
                    tbar.update(1)
                    self._reports.pop(0)
                    continue

                try:
                    report_to_mangadex(report)
                except requests.HTTPError:
                    logger.warning("Could not submit report to mangadex! Skipping...")
                    tbar.update(1)
                    self._reports.pop(0)
                    continue

                tbar.update(1)
                self._reports.pop(0)

        self._reporting = False

    def _init_report(self):
        if not self._reporting:
            self._report_total = 1
            logging.debug("Starting new reporter thread")
            thread = threading.Thread(target=self._report)
            thread.start()

    def add_report(self, report: ReportInfo):
        """
        Adds the report to the queue to be processed

        Arguments:
            report (mangadex_dl.ReportInfo): the report to add to the queue
        """
        self._reports.append(report)
        self._report_total += 1
        self._init_report()


def report_to_mangadex(report: ReportInfo):
    """
    Report the given report to mangadex

    Arguments:
        report (mangadex_dl.ReportInfo): the report to add to the queue
    """
    report_url = "https://api.mangadex.network/report"
    response = requests.post(report_url, data=report)

    while response.status_code == 429:
        wait_time = int(
            int(response.headers.get("x-ratelimit-retry-after", int(time() + 60)))
            - time()
        )

        logger.warning(
            "Exceeded rate-limit for reporting, waiting %i seconds", wait_time
        )
        sleep(wait_time)

        response = requests.post(report_url, data=report)

    if response.status_code != 200:
        response.raise_for_status()

    rate_limit = int(response.headers.get("x-ratelimit-limit") or 0)
    sleep(60 / rate_limit)
