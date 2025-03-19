import os
import re
import sys

import arrow
import cachetools.func
import cherrypy
import requests
from ics import Calendar

from log import setup_logging

log = setup_logging("rewe-lieferung")


url = os.environ.get("CALENDAR_URL")
zipCode = os.environ.get("ZIP_CODE")


def get_ics():
    log.debug("Fetching calendar")
    return requests.get(url).text


@cachetools.func.ttl_cache(maxsize=1, ttl=3600)
def get_calendar():
    log.debug("Parsing calendar")
    return Calendar(get_ics())


def get_delivery_id():
    log.debug("Searching for delivery")
    for e in get_calendar().timeline.on(arrow.now()):
        log.debug(e.name)
        if re.search(r"REWE", e.name):
            log.debug("Found delivery event", description=e.description)
            return re.search("wannkommt\.rewe\.de/([^\"]+)", e.description).group(1)

    return None


def get_delivery_status():
    delivery_id = get_delivery_id()
    if delivery_id is None:
        log.warn("No delivery found")
        return {"status": "NO_DELIVERY"}

    log.info("Delivery found", delivery_id=delivery_id)

    delivery = requests.post(
        f'https://wannkommt.rewe.de/api/delivery/{delivery_id}',
        headers={'Accept': 'application/json, text/plain, */*'},
        json={'zipCode': zipCode},
    ).json()

    log.debug("Delivery status", delivery=delivery)

    return (
        {
            "status": delivery["orderStatusList"][0]["status"],
        }
        | (
            {
                "customersBefore": delivery["customersBeforeMe"],
            }
            if delivery["customersBeforeMe"]
            else {}
        )
        | (
            {
                "expectedArrivalIntervalStart": delivery["expectedArrivalIntervalStart"],
            }
            if delivery["expectedArrivalIntervalStart"]
            else {}
        )
    )


class REWE:
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def index(self):
        return get_delivery_status()


if __name__ == "__main__":
    cherrypy.config.update({"server.socket_host": "0.0.0.0", "server.socket_port": 12345})
    cherrypy.quickstart(REWE())
