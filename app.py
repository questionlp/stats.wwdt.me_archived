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

#region Error Routes
def error_500(error):
    return render_template_string(error)

#endregion

#region Guest Routes
@app.route("/guests")
def get_guests():
    return render_template_string("guests")

@app.route("/guests/<string:guest>")
def get_guests_details(guest: Text):
    guest_slug = slugify(guest)
    return render_template_string("guests: {{ guest_slug }}", guest_slug=guest_slug)

#endregion



#region Host Routes
@app.route("/hosts")
def get_hosts():
    return render_template_string("hosts")

@app.route("/hosts/<string:host>")
def get_hosts_details(host: Text):
    host_slug = slugify(host)
    return render_template_string("hosts: {{ host_slug }}", host_slug=host_slug)

#endregion



#region Panelist Routes
@app.route("/panelists")
def get_panelists():
    return

@app.route("/panelists/<string:panelist>")
def get_panelists_details(panelist: Text):
    panelist_slug = slugify(panelist)
    return

#endregion



#region Scorekeeper Routes
@app.route("/scorekeepers")
def get_scorekeepers():
    return

@app.route("/scorekeepers/<string:scorekeeper>")
def get_scorekeepers_details(scorekeeper: Text):
    scorekeeper_slug = slugify(scorekeeper)
    return

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
