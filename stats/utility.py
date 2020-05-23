# -*- coding: utf-8 -*-
# Copyright (c) 2018-2020 Linh Pham
# stats.wwdt.me is relased under the terms of the Apache License 2.0
"""Time Zone Parser functions used by the Stats Page"""

import pytz

#region Utility Functions
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
