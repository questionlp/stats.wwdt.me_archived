# -*- coding: utf-8 -*-
# Copyright (c) 2018-2021 Linh Pham
# stats.wwdt.me is relased under the terms of the Apache License 2.0
"""Retrieve random items from Stats Page database"""

import mysql.connector

#region Retrieve Functions
def random_guest_slug(database_connection: mysql.connector.connect) -> str:
    """Return a random guest slug from ww_guests table"""

    database_connection.reconnect()
    cursor = database_connection.cursor(dictionary=True)
    query = ("SELECT g.guestslug FROM ww_guests g "
             "WHERE g.guestslug <> 'none' "
             "ORDER BY RAND() "
             "LIMIT 1;")
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()

    if not result:
        return None

    return result["guestslug"]

def random_host_slug(database_connection: mysql.connector.connect) -> str:
    """Return a random host slug from ww_hosts table"""

    database_connection.reconnect()
    cursor = database_connection.cursor(dictionary=True)
    query = ("SELECT h.hostslug FROM ww_hosts h "
             "WHERE h.hostslug <> 'tbd' "
             "ORDER BY RAND() "
             "LIMIT 1;")
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()

    if not result:
        return None

    return result["hostslug"]

def random_location_slug(database_connection: mysql.connector.connect) -> str:
    """Return a random location slug from ww_locations table"""

    database_connection.reconnect()
    cursor = database_connection.cursor(dictionary=True)
    query = ("SELECT l.locationslug FROM ww_locations l "
             "WHERE l.locationslug <> 'tbd' "
             "ORDER BY RAND() "
             "LIMIT 1;")
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()

    if not result:
        return None

    return result["locationslug"]

def random_panelist_slug(database_connection: mysql.connector.connect) -> str:
    """Return a random panelist slug from ww_panelists table"""

    database_connection.reconnect()
    cursor = database_connection.cursor(dictionary=True)
    query = ("SELECT p.panelistslug FROM ww_panelists p "
             "WHERE p.panelistslug <> 'multiple' "
             "ORDER BY RAND() "
             "LIMIT 1;")
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()

    if not result:
        return None

    return result["panelistslug"]

def random_scorekeeper_slug(database_connection: mysql.connector.connect) -> str:
    """Return a random scorekeeper slug from ww_scorekeepers table"""

    database_connection.reconnect()
    cursor = database_connection.cursor(dictionary=True)
    query = ("SELECT sk.scorekeeperslug FROM ww_scorekeepers sk "
             "WHERE sk.scorekeeperslug <> 'tbd' "
             "ORDER BY RAND() "
             "LIMIT 1;")
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()

    if not result:
        return None

    return result["scorekeeperslug"]

def random_show_date(database_connection: mysql.connector.connect) -> str:
    """Return a random show date from the ww_shows table"""

    database_connection.reconnect()
    cursor = database_connection.cursor(dictionary=True)
    query = ("SELECT s.showdate FROM ww_shows s "
             "WHERE s.showdate <= NOW() "
             "ORDER BY RAND() "
             "LIMIT 1;")
    cursor.execute(query)
    result = cursor.fetchone()
    cursor.close()

    if not result:
        return None

    return result["showdate"].isoformat()

#endregion
