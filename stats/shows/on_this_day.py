# -*- coding: utf-8 -*-
# Copyright (c) 2018-2020 Linh Pham
# stats.wwdt.me is relased under the terms of the Apache License 2.0
"""On This Show functions used by the Stats Page"""

from typing import List

import mysql.connector

#region Retrieval Functions
def retrieve_on_this_day_show_ids(database_connection: mysql.connector.connect) -> List[int]:
    """Returns a list of show IDs for shows that broadcasted on this
    day in previous years"""

    show_ids = []
    database_connection.reconnect()
    cursor = database_connection.cursor(dictionary=True)
    query = ("SELECT s.showid FROM ww_shows s "
             "WHERE MONTH(s.showdate) = MONTH(NOW()) "
             "AND DAY(s.showdate) = DAY(NOW()) "
             "ORDER BY s.showdate ASC;")
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()

    if not result:
        return None

    for row in result:
        show_ids.append(row["showid"])

    return show_ids

#endregion
