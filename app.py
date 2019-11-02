# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 Linh Pham
# stats.wwdt.me is relased under the terms of the Apache License 2.0
"""Flask application startup file"""

from datetime import datetime
import json
import os
import pytz
from typing import Optional, Text

from flask import (Flask, abort, redirect, render_template,
                   render_template_string, request, url_for)
import mysql.connector
from slugify import slugify
from wwdtm import (guest as ww_guest, host as ww_host, panelist as ww_panelist,
                   scorekeeper as ww_scorekeeper, show as ww_show)

#region Flask App Initialization
app = Flask(__name__)
app.url_map.strict_slashes = False

# Override base Jinja options
jinja_options = Flask.jinja_options.copy()
app.jinja_options.update({"trim_blocks": True, "lstrip_blocks": True})
app.create_jinja_environment()

#endregion

#region Global Variables
ga_property_code = None
#endregion

#region Bootstrap Functions
def load_config():
    """Load configuration settings from config.json"""

    global ga_property_code

    with open("config.json", "r") as config_file:
        config_dict = json.load(config_file)

    # Set the ga_property_code global variable
    ga_property_code = config_dict["settings"]["ga_property_code"]

    return config_dict

#endregion

#region Common Functions
def generate_date_time_stamp():
    """Generate a current date/timestamp string"""
    now = datetime.now(time_zone)
    return now.strftime("%A, %B %d, %Y %H:%M:%S %Z")

#endregion

#region Filters
@app.template_filter("rankify")
def panelist_rank_format(rank: Text):
    rank_label = {
        "1": "First",
        "1t": "First Tied",
        "2": "Second",
        "2t": "Second Tied",
        "3": "Third"
    }
    return rank_label[rank]

#endregion

#region Error Routes
def error_500(error):
    return render_template_string(error)

#endregion

#region Guest Routes
@app.route("/guests")
def get_guests():
    database_connection.reconnect()
    guests_list = ww_guest.info.retrieve_all(database_connection)
    if guests_list:
        return render_template_string("<pre>{{g}}</pre>", g=json.dumps(guests_list, indent=1))

@app.route("/guests/<string:guest>")
def get_guests_details(guest: Text):
    database_connection.reconnect()
    guest_slug = slugify(guest)
    guest_details = ww_guest.details.retrieve_by_slug(guest_slug, database_connection)
    if guest_details:
        return render_template_string("<pre>{{g}}</pre>", g=json.dumps(guest_details, indent=1))
    else:
        return render_template_string("{{gs}} not found", gs=guest_slug)

#endregion



#region Host Routes
@app.route("/hosts")
def get_hosts():
    database_connection.reconnect()
    hosts_list = ww_host.info.retrieve_all(database_connection)
    if hosts_list:
        return render_template_string("<pre>{{h}}</pre>", h=json.dumps(hosts_list, indent=1))

@app.route("/hosts/<string:host>")
def get_hosts_details(host: Text):
    database_connection.reconnect()
    host_slug = slugify(host)
    host_details = ww_host.details.retrieve_by_slug(host_slug, database_connection)
    if host_details:
        return render_template_string("<pre>{{h}}</pre>", h=json.dumps(host_details, indent=1))
    else:
        return render_template_string("{{ hs }} not found", hs=host_slug)

#endregion



#region Panelist Routes
@app.route("/panelists")
def get_panelists():
    database_connection.reconnect()
    panelists_list = ww_panelist.details.retrieve_all(database_connection)
    if panelists_list:
        return render_template("panelists/index.html", panelists_list=panelists_list)
        #return render_template_string("<pre>{{p}}</pre>", p=json.dumps(panelists_list, indent=1))

@app.route("/panelists/<string:panelist>")
def get_panelists_details(panelist: Text):
    database_connection.reconnect()
    panelist_slug = slugify(panelist)
    if panelist != panelist_slug:
        return redirect(url_for('get_panelists_details', panelist=panelist_slug))
    panelist_details = ww_panelist.details.retrieve_by_slug(panelist_slug, database_connection)
    if panelist_details:
        return render_template("panelists/details.html", panelist=panelist_details)

#endregion



#region Scorekeeper Routes
@app.route("/scorekeepers")
def get_scorekeepers():
    return

@app.route("/scorekeepers/<string:scorekeeper>")
def get_scorekeepers_details(scorekeeper: Text):
    database_connection.reconnect()
    scorekeeper_slug = slugify(scorekeeper)
    scorekeeper_details = ww_scorekeeper.details.retrieve_by_slug(scorekeeper_slug, database_connection)
    if scorekeeper_details:
        return render_template_string("{{ sk }}", sk=json.dumps(scorekeeper_details))
    else:
        return render_template_string("{{ sks }} not found", sks=scorekeeper_slug)

#endregion


#region Show Routes
@app.route("/shows")
def get_shows():
    return

@app.route("/shows/<int:year>")
def get_shows_year(year: int):
    return

@app.route("/shows/<int:year>/<int:month>")
def get_shows_year_month(year: int, month: int):
    return


@app.route("/shows/<int:year>/<int:month>/<int:day>")
def get_shows_year_month_day(year: int, month: int, day: int):
    return

@app.route("/shows/<int:year>/all")
def get_shows_year_all(year: int):
    return

@app.route("/shows/recent")
def get_shows_recent():
    return

#endregion





#region Application Initialization
config_dict = load_config()
database_connection = mysql.connector.connect(**config_dict["database"])
database_connection.autocommit = True
time_zone = pytz.timezone("America/Los_Angeles")


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port="9248")

#endregion
