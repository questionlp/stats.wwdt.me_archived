# -*- coding: utf-8 -*-
# Copyright (c) 2018-2020 Linh Pham
# stats.wwdt.me is relased under the terms of the Apache License 2.0
"""Time Zone Parser functions used by the Stats Page"""

from datetime import datetime
from dateutil import parser
import pytz

#region Date/Time Functions
def current_year(time_zone: pytz.timezone = pytz.timezone("UTC")):
    """Return the current year"""
    now = datetime.now(time_zone)
    return now.strftime("%Y")

def date_string_to_date(**kwargs):
    """Used to convert an ISO-style date string into a datetime object"""
    if "date_string" in kwargs and kwargs["date_string"]:
        try:
            date_object = parser.parse(kwargs["date_string"])
            return date_object

        except ValueError:
            return None

    return None

def generate_date_time_stamp(time_zone: pytz.timezone = pytz.timezone("UTC")):
    """Generate a current date/timestamp string"""
    now = datetime.now(time_zone)
    return now.strftime("%Y-%m-%d %H:%M:%S %Z")


def time_zone_parser(time_zone: str) -> pytz.timezone:
    """Parses a time zone name into a pytz.timezone object"""

    try:
        time_zone_obj = pytz.timezone(time_zone)
        time_zone_name = time_zone_obj.zone
    except (pytz.UnknownTimeZoneError, AttributeError, ValueError):
        time_zone_obj = pytz.timezone("UTC")
        time_zone_name = time_zone_obj.zone

    return time_zone_obj, time_zone_name

#endregion
