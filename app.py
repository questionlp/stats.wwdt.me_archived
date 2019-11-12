# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 Linh Pham
# stats.wwdt.me is relased under the terms of the Apache License 2.0
"""Flask application startup file"""

from datetime import date, datetime
from dateutil import parser
import json
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

def retrieve_show_years(reverse_order: bool = True):
    """Retrieve list of available show years"""
    database_connection.reconnect()
    years = ww_show.info.retrieve_years(database_connection)
    if reverse_order:
        years.reverse()

    return years

def date_string_to_date(date_string: Text):
    try:
        date = parser.parse(date_string)
        return date
    except:
        return None

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

@app.template_filter("pretty_jsonify")
def pretty_jsonify(data):
    return json.dumps(data, indent=2)

#endregion

#region Error Routes
def error_500(error):
    return render_template_string(error)

#endregion

#region General Redirect Routes
@app.route("/location")
def get_location():
    return redirect(url_for("index"))

#region Default Routes
@app.route("/")
def index():
    database_connection.reconnect()
    recent_shows = ww_show.details.retrieve_recent(database_connection)
    recent_shows.reverse()
    return render_template("index.html",
                           date_string_to_date=date_string_to_date,
                           show_years=retrieve_show_years(),
                           shows=recent_shows,
                           ga_property_code=ga_property_code,
                           rendered_at=generate_date_time_stamp())

#endregion


#region Guest Routes
@app.route("/guest")
def get_guest():
    return redirect(url_for("get_guests"), code=301)

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
@app.route("/host")
def get_host():
    return redirect(url_for("get_hosts"), code=301)

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
@app.route("/panelist")
def get_panelist():
    return redirect(url_for("get_panelists"), code=301)

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
@app.route("/scorekeeper")
def get_scorekeeper():
    return redirect(url_for("get_scorekeepers"), code=301)

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
@app.route("/show")
def get_show():
    return redirect(url_for("get_shows"), code=301)

@app.route("/shows")
def get_shows():
    database_connection.reconnect()
    show_years = retrieve_show_years()
    return render_template("shows/shows.html",
                           show_years=show_years,
                           ga_property_code=ga_property_code,
                           rendered_at=generate_date_time_stamp())

@app.route("/shows/<int:year>")
def get_shows_year(year: int):
    try:
        database_connection.reconnect()
        date_year = date(year=year, month=1, day=1)
        show_months = ww_show.info.retrieve_months_by_year(show_year=year,
                                                           database_connection=database_connection)
        months = []
        for month in show_months:
            months.append(date(year=year, month=month, day=1))

        return render_template("shows/year.html",
                               date_string_to_date=date_string_to_date,
                               year=date_year,
                               show_months=months,
                               ga_property_code=ga_property_code,
                               rendered_at=generate_date_time_stamp())
    except:
        return redirect(url_for("get_shows"))

@app.route("/shows/<string:show_date>")
def get_shows_date(show_date: Text):
    try:
        parsed_date = parser.parse(show_date)
        return redirect(url_for("get_shows_year_month_day",
                                date_string_to_date=date_string_to_date,
                                year=parsed_date.year,
                                month=parsed_date.month,
                                day=parsed_date.day,
                                ), code=301)
    except:
        return redirect(url_for("get_shows"))

@app.route("/shows/<int:year>/<int:month>")
def get_shows_year_month(year: int, month: int):
    try:
        database_connection.reconnect()
        year_month = date(year=year, month=month, day=1)
        show_list = ww_show.details.retrieve_by_year_month(show_year=year,
                                                       show_month=month,
                                                       database_connection=database_connection)
        if not show_list:
            return redirect(url_for("index"))

        return render_template("shows/year_month.html",
                               date_string_to_date=date_string_to_date,
                               show_years=retrieve_show_years(),
                               year_month=year_month,
                               shows=show_list,
                               ga_property_code=ga_property_code,
                               rendered_at=generate_date_time_stamp())
    except:
        return redirect(url_for("get_shows_year", year=year))

@app.route("/shows/<int:year>/<int:month>/<int:day>")
def get_shows_year_month_day(year: int, month: int, day: int):
    try:
        database_connection.reconnect()
        show_list = []
        today = date(year=year, month=month, day=day)
        details = ww_show.details.retrieve_by_date(show_year=year,
                                                   show_month=month,
                                                   show_day=day,
                                                   database_connection=database_connection)
        if not details:
            return redirect(url_for("index"))

        show_list.append(details)
        return render_template("shows/single.html",
                               date_string_to_date=date_string_to_date,
                               show_years=retrieve_show_years(),
                               today=today,
                               shows=show_list,
                               ga_property_code=ga_property_code,
                               rendered_at=generate_date_time_stamp())
    except:
        return redirect(url_for("get_shows"))

@app.route("/shows/<int:year>/all")
def get_shows_year_all(year: int):
    try:
        database_connection.reconnect()
        shows_list = ww_show.details.retrieve_by_year(show_year=year,
                                                      database_connection=database_connection)
        if not shows_list:
            return redirect(url_for("get_shows_year", year=year))

        return render_template("shows/year_all.html",
                               date_string_to_date=date_string_to_date,
                               year=year,
                               shows=shows_list,
                               ga_property_code=ga_property_code,
                               rendered_at=generate_date_time_stamp())
    except:
        return redirect(url_for("get_shows"))

@app.route("/shows/recent")
def get_shows_recent():
    return redirect(url_for("index"))

#endregion


#region NPR Show Redirect Routes
@app.route("/s/<string:show_date>")
def npr_show_redirect(show_date: Text):
    show_date_object = date_string_to_date(show_date)
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
config_dict = load_config()
ga_property_code = config_dict["settings"]["ga_property_code"]
database_connection = mysql.connector.connect(**config_dict["database"])
database_connection.autocommit = True
time_zone = pytz.timezone("America/Los_Angeles")

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port="9248")

#endregion
