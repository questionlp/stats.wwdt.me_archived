# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 Linh Pham
# stats.wwdt.me is relased under the terms of the Apache License 2.0
"""Flask application startup file"""

from datetime import date, datetime
import json
from typing import Text
import traceback

from dateutil import parser
from flask import Flask, redirect, render_template, url_for
from flask.logging import create_logger
import mysql.connector
import pytz
from slugify import slugify
from werkzeug.exceptions import HTTPException
from wwdtm import (guest as ww_guest, host as ww_host, panelist as ww_panelist,
                   scorekeeper as ww_scorekeeper, show as ww_show)

#region Global Constants
APP_VERSION = "4.0rc1"

#endregion

#region Flask App Initialization
app = Flask(__name__)
app.url_map.strict_slashes = False
app_logger = create_logger(app)

# Override base Jinja options
app.jinja_options = Flask.jinja_options.copy()
app.jinja_options.update({"trim_blocks": True, "lstrip_blocks": True})
app.create_jinja_environment()

#endregion

#region Bootstrap Functions
def load_config():
    """Load configuration settings from config.json"""
    with open("config.json", "r") as config_file:
        config_dict = json.load(config_file)

    return config_dict

#endregion

#region Common Functions
def generate_date_time_stamp(time_zone: pytz.timezone = pytz.timezone("UTC")):
    """Generate a current date/timestamp string"""
    now = datetime.now(time_zone)
    return now.strftime("%Y-%m-%d %H:%M:%S %Z")

def retrieve_show_years(reverse_order: bool = True):
    """Retrieve list of available show years"""
    database_connection.reconnect()
    years = ww_show.info.retrieve_years(database_connection)
    if reverse_order:
        years.reverse()

    return years

def date_string_to_date(**kwargs):
    """Used to convert an ISO-style date string into a datetime object"""
    try:
        if "date_string" in kwargs:
            if kwargs["date_string"]:
                date_object = parser.parse(kwargs["date_string"])
                return date_object
            else:
                return None
    except ValueError:
        return None

#endregion

#region Filters
@app.template_filter("rankify")
def panelist_rank_format(rank: Text):
    """Convert panelist ranking shorthand into full rank name"""
    rank_label = {
        "1": "First",
        "1t": "First Tied",
        "2": "Second",
        "2t": "Second Tied",
        "3": "Third"
    }
    return rank_label[rank]

@app.template_filter("pretty_jsonify")
def pretty_jsonify(data):
    """Returns a prettier JSON output for an object than Flask's default
    tojson filter"""
    return json.dumps(data, indent=2)

#endregion

#region Error Handlers
@app.errorhandler(Exception)
def handle_exception(error):
    """Handle exceptions in a slightly more graceful manner"""
    # Pass through any HTTP errors and exceptions
    if isinstance(error, HTTPException):
        return error

    # Handle everything else with a basic 500 error page
    error_traceback = traceback.format_exc()
    app_logger.error(error_traceback)
    return render_template("errors/500.html",
                           error_traceback=error_traceback), 500

#endregion

#region General Redirect Routes
@app.route("/help")
def help_page():
    """Redirecting /help to /"""
    return redirect(url_for("index"))

@app.route("/location")
def get_location():
    """Placeholder for future show location view"""
    return redirect(url_for("index"))

@app.route("/search")
def search_page():
    """Redirecting /search to /"""
    return redirect(url_for("index"))

#endregion

#region Default Route
@app.route("/")
def index():
    """Default page that includes details for recent shows"""
    database_connection.reconnect()
    recent_shows = ww_show.details.retrieve_recent(database_connection)
    recent_shows.reverse()
    return render_template("pages/index.html",
                           shows=recent_shows)

#endregion

#region Site Information Routes
@app.route("/about")
def about():
    """About Page"""
    return render_template("pages/about.html")

@app.route("/site-history")
def site_history():
    """Site History Page"""
    return render_template("pages/site_history.html")

#endregion


#region Guest Routes
@app.route("/guest")
def get_guest():
    """Redirect /guest to /guests"""
    return redirect(url_for("get_guests"), code=301)

@app.route("/guests")
def get_guests():
    """Presents a list of Not My Job guests"""
    database_connection.reconnect()
    guests_list = ww_guest.info.retrieve_all(database_connection)

    if guests_list:
        return render_template("guests/guests.html",
                               guests=guests_list)
    else:
        return redirect(url_for("index"))


@app.route("/guests/<string:guest>")
def get_guest_details(guest: Text):
    """Presents appearance details for a Not My Job guest"""
    guest_slug = slugify(guest)
    if guest and guest != guest_slug:
        return redirect(url_for("get_guest_details", guest=guest_slug))

    database_connection.reconnect()
    guest_details = ww_guest.details.retrieve_by_slug(guest_slug,
                                                      database_connection)

    if guest_details:
        # Template expects a list of guests(s)
        guests = []
        guests.append(guest_details)
        return render_template("guests/single.html",
                               guest_name=guest_details["name"],
                               guests=guests)
    else:
        return redirect(url_for("get_guests"))


@app.route("/guests/all")
def get_guests_all():
    """Presents appearance details for all Not My Job guests"""
    database_connection.reconnect()
    guests = ww_guest.details.retrieve_all(database_connection)

    if guests:
        return render_template("guests/all.html",
                               guests=guests)
    else:
        return redirect(url_for("get_guests"))

#endregion


#region Host Routes
@app.route("/host")
def get_host():
    """Redirect /host to /hosts"""
    return redirect(url_for("get_hosts"), code=301)

@app.route("/hosts")
def get_hosts():
    """Presents a list of show hosts"""
    database_connection.reconnect()
    hosts_list = ww_host.info.retrieve_all(database_connection)

    if hosts_list:
        return render_template("hosts/hosts.html",
                               hosts=hosts_list)
    else:
        return redirect(url_for("index"))

@app.route("/hosts/<string:host>")
def get_host_details(host: Text):
    """Presents appearance details for a show host"""
    database_connection.reconnect()
    host_slug = slugify(host)
    if host and host != host_slug:
        return redirect(url_for("get_host_details", host=host_slug))

    host_details = ww_host.details.retrieve_by_slug(host_slug,
                                                    database_connection)

    if host_details:
        # Template expects a list of hosts(s)
        hosts = []
        hosts.append(host_details)
        return render_template("hosts/single.html",
                               host_name=host_details["name"],
                               hosts=hosts)
    else:
        return redirect(url_for("get_hosts"))

@app.route("/hosts/all")
def get_hosts_all():
    """Presents appearance details for all show hosts"""
    database_connection.reconnect()
    hosts = ww_host.details.retrieve_all(database_connection)

    if hosts:
        return render_template("hosts/all.html",
                               hosts=hosts)
    else:
        return redirect(url_for("get_hosts"))

#endregion


#region Panelist Routes
@app.route("/panelist")
def get_panelist():
    """Redirect /panelist to /panelists"""
    return redirect(url_for("get_panelists"), code=301)

@app.route("/panelists")
def get_panelists():
    """Presents a list of panelists"""
    database_connection.reconnect()
    panelist_list = ww_panelist.info.retrieve_all(database_connection)

    if panelist_list:
        return render_template("panelists/panelists.html",
                               panelists=panelist_list)
    else:
        return redirect(url_for("index"))

@app.route("/panelists/<string:panelist>")
def get_panelist_details(panelist: Text):
    """Presents statistics and appearance details for a panelist"""
    database_connection.reconnect()
    panelist_slug = slugify(panelist)
    if panelist and panelist != panelist_slug:
        return redirect(url_for("get_panelist_details",
                                panelist=panelist_slug))

    panelist_details = ww_panelist.details.retrieve_by_slug(panelist_slug,
                                                            database_connection)

    if panelist_details:
        # Template expects a list of panelists(s)
        panelists = []
        panelists.append(panelist_details)
        return render_template("panelists/single.html",
                               panelist_name=panelist_details["name"],
                               panelists=panelists)
    else:
        return redirect(url_for("get_panelists"))

@app.route("/panelists/all")
def get_panelists_all():
    """Presents statistics and appearance details for all panelists"""
    database_connection.reconnect()
    panelists = ww_panelist.details.retrieve_all(database_connection)

    if panelists:
        return render_template("panelists/all.html",
                               panelists=panelists)
    else:
        return redirect(url_for("get_panelists"))

#endregion


#region Scorekeeper Routes
@app.route("/scorekeeper")
def get_scorekeeper():
    """Redirect /scorekeeper to /scorekeepers"""
    return redirect(url_for("get_scorekeepers"), code=301)

@app.route("/scorekeepers")
def get_scorekeepers():
    """Presents a list of scorekeepers"""
    database_connection.reconnect()
    scorekeepers_list = ww_scorekeeper.info.retrieve_all(database_connection)
    if scorekeepers_list:
        return render_template("scorekeepers/scorekeepers.html",
                               scorekeepers=scorekeepers_list)
    else:
        return redirect(url_for("index"))

@app.route("/scorekeepers/<string:scorekeeper>")
def get_scorekeeper_details(scorekeeper: Text):
    """Presents appearance details for a scorekeeper"""
    database_connection.reconnect()
    scorekeeper_slug = slugify(scorekeeper)
    if scorekeeper and scorekeeper != scorekeeper_slug:
        return redirect(url_for("get_scorekeeper_details",
                                scorekeeper=scorekeeper_slug))

    scorekeeper_details = ww_scorekeeper.details.retrieve_by_slug(scorekeeper_slug,
                                                                  database_connection)

    if scorekeeper_details:
        # Template expects a list of scorekeepers(s)
        scorekeepers = []
        scorekeepers.append(scorekeeper_details)
        return render_template("scorekeepers/single.html",
                               scorekeeper_name=scorekeeper_details["name"],
                               scorekeepers=scorekeepers)
    else:
        return redirect(url_for("get_scorekeepers"))

@app.route("/scorekeepers/all")
def get_scorekeepers_all():
    """Presents appearance details for all scorekeepers"""
    database_connection.reconnect()
    scorekeepers = ww_scorekeeper.details.retrieve_all(database_connection)
    if scorekeepers:
        return render_template("scorekeepers/all.html",
                               scorekeepers=scorekeepers)
    else:
        return redirect(url_for("get_scorekeepers"))

#endregion


#region Show Routes
@app.route("/show")
def get_show():
    """Redirect /show to /shows"""
    return redirect(url_for("get_shows"), code=301)

@app.route("/shows")
def get_shows():
    """Presents a list of available show years"""
    database_connection.reconnect()
    show_years = retrieve_show_years()

    if show_years:
        return render_template("shows/shows.html",
                               show_years=show_years)
    else:
        return redirect(url_for("index"))

@app.route("/shows/<int:year>")
def get_shows_year(year: int):
    """Presents a list of available show months for a given year"""
    database_connection.reconnect()
    date_year = date(year=year, month=1, day=1)
    show_months = ww_show.info.retrieve_months_by_year(show_year=year,
                                                       database_connection=database_connection)
    months = []
    for month in show_months:
        months.append(date(year=year, month=month, day=1))

    return render_template("shows/year.html",
                           year=date_year,
                           show_months=months)

@app.route("/shows/<string:show_date>")
def get_shows_date(show_date: Text):
    """Convert an ISO-like date string into a datetime value and
    redirect the request with the parsed year, month and day"""
    try:
        parsed_date = parser.parse(show_date)
        return redirect(url_for("get_show_year_month_day",
                                year=parsed_date.year,
                                month=parsed_date.month,
                                day=parsed_date.day,
                                ), code=301)
    except ValueError:
        return redirect(url_for("get_shows"))

@app.route("/shows/<int:year>/<int:month>")
def get_shows_year_month(year: int, month: int):
    """Presents a list of available shows for a given year and month"""
    database_connection.reconnect()
    year_month = date(year=year, month=month, day=1)
    show_list = ww_show.details.retrieve_by_year_month(show_year=year,
                                                       show_month=month,
                                                       database_connection=database_connection)
    if not show_list:
        return redirect(url_for("index"))

    print(show_list)
    return render_template("shows/year_month.html",
                           year_month=year_month,
                           shows=show_list)

@app.route("/shows/<int:year>/<int:month>/<int:day>")
def get_show_year_month_day(year: int, month: int, day: int):
    """Presents show details for a given year, month and day"""
    database_connection.reconnect()
    today = date(year=year, month=month, day=day)
    details = ww_show.details.retrieve_by_date(show_year=year,
                                               show_month=month,
                                               show_day=day,
                                               database_connection=database_connection)
    if details:
        # Template expects a list of show(s)
        show_list = []
        show_list.append(details)
        return render_template("shows/single.html",
                               today=today,
                               shows=show_list)
    else:
        return redirect(url_for("get_shows"))

@app.route("/shows/<int:year>/all")
def get_shows_year_all(year: int):
    """Presents details for all shows available"""
    database_connection.reconnect()
    shows_list = ww_show.details.retrieve_by_year(show_year=year,
                                                  database_connection=database_connection)
    if not shows_list:
        return redirect(url_for("get_shows_year", year=year))

    return render_template("shows/year_all.html",
                           year=year,
                           shows=shows_list)

@app.route("/shows/recent")
def get_shows_recent():
    """Redirects /shows/recent to / as the index page presents a list
    of recent show details"""
    return redirect(url_for("index"))

#endregion


#region NPR Show Redirect Routes
@app.route("/s/<string:show_date>")
def npr_show_redirect(show_date: Text):
    """Takes an ISO-like date string and redirects to the appropriate
    show page on NPR's website."""
    show_date_object = date_string_to_date(date_string=show_date)

    if not show_date_object:
        return redirect(url_for("index"))

    if ww_show.utility.date_exists(show_year=show_date_object.year,
                                   show_month=show_date_object.month,
                                   show_day=show_date_object.day,
                                   database_connection=database_connection):
        current_url_prefix = "http://www.npr.org/programs/wait-wait-dont-tell-me/archive?date="
        legacy_url_prefix = "http://www.npr.org/programs/waitwait/archrndwn"
        legacy_url_suffix = ".waitwait.html"
        if show_date_object >= datetime(year=2006, month=1, day=7):
            show_date_string = show_date_object.strftime("%m-%d-%Y")
            url = f"{current_url_prefix}{show_date_string}"
        else:
            show_date_string = show_date_object.strftime("%y%m%d")
            year = show_date_object.strftime("%Y")
            month = show_date_object.strftime("%b").lower()
            url = f"{legacy_url_prefix}/{year}/{month}/{show_date_string}{legacy_url_suffix}"

    return redirect(url)

#endregion

#region Application Initialization
config = load_config()
app.jinja_env.globals["app_version"] = APP_VERSION
app.jinja_env.globals["current_date"] = date.today()
app.jinja_env.globals["date_string_to_date"] = date_string_to_date
app.jinja_env.globals["ga_property_code"] = config["settings"]["ga_property_code"]
app.jinja_env.globals["rendered_at"] = generate_date_time_stamp()
database_connection = mysql.connector.connect(**config["database"])
database_connection.autocommit = True

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port="9248")

#endregion
