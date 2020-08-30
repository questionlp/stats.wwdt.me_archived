# -*- coding: utf-8 -*-
# Copyright (c) 2018-2020 Linh Pham
# stats.wwdt.me is relased under the terms of the Apache License 2.0
"""Flask application startup file"""

from collections import OrderedDict
from datetime import date, datetime
import json
from typing import Text
import traceback

from dateutil import parser
from flask import Flask, redirect, render_template, Response, url_for
from flask.logging import create_logger
import mysql.connector
import pytz
from slugify import slugify
from werkzeug.exceptions import HTTPException
from wwdtm import (guest as ww_guest, host as ww_host,
                   location as ww_location, panelist as ww_panelist,
                   scorekeeper as ww_scorekeeper, show as ww_show)
from wwdtm import VERSION as WWDTM_VERSION
from stats import dicts, utility
from stats.shows import on_this_day
from stats.locations import formatting

#region Global Constants
APP_VERSION = "4.4.3"

DEFAULT_RECENT_DAYS_AHEAD = 2
DEFAULT_RECENT_DAYS_BACK = 30
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

    if "time_zone" in config_dict["settings"] and config_dict["settings"]["time_zone"]:
        time_zone = config_dict["settings"]["time_zone"]
        time_zone_object, time_zone_string = utility.time_zone_parser(time_zone)

        config_dict["settings"]["app_time_zone"] = time_zone_object
        config_dict["settings"]["time_zone"] = time_zone_string
        config_dict["database"]["time_zone"] = time_zone_string
    else:
        config_dict["settings"]["app_time_zone"] = pytz.timezone("UTC")
        config_dict["settings"]["time_zone"] = "UTC"
        config_dict["database"]["time_zone"] = "UTC"

    return config_dict

#endregion

#region Common Functions
def retrieve_show_dates(reverse_order: bool = False):
    """Retrieve a list of available show dates"""
    database_connection.reconnect()
    show_dates = ww_show.info.retrieve_all_dates_tuple(database_connection)
    if show_dates and reverse_order:
        show_dates.reverse()

    return show_dates

def retrieve_show_years(reverse_order: bool = True):
    """Retrieve a list of available show years"""
    database_connection.reconnect()
    years = ww_show.info.retrieve_years(database_connection)
    if years and reverse_order:
        years.reverse()

    return years

def retrieve_show_years_months(reverse_order: bool = False):
    """Retrieve a list of available show years and months"""
    database_connection.reconnect()
    years_months = ww_show.info.retrieve_all_show_years_months_tuple(database_connection)
    if years_months and reverse_order:
        years_months.reverse()

    return years_months

#endregion

#region Filters
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

    try:
        if "recent_days_ahead" in config["settings"]:
            days_ahead = int(config["settings"]["recent_days_ahead"])
        else:
            days_ahead = DEFAULT_RECENT_DAYS_AHEAD
    except TypeError:
        app_logger.warning("Invalid value type in settings.recent_days_ahead. "
                           "Using default value of %s", DEFAULT_RECENT_DAYS_AHEAD)
        days_ahead = DEFAULT_RECENT_DAYS_AHEAD
    except ValueError:
        app_logger.warning("Invalid value in settings.recent_days_ahead. "
                           "Using default value of %s", DEFAULT_RECENT_DAYS_AHEAD)
        days_ahead = DEFAULT_RECENT_DAYS_AHEAD

    try:
        if "recent_days_back" in config["settings"]:
            days_back = int(config["settings"]["recent_days_back"])
        else:
            days_back = DEFAULT_RECENT_DAYS_BACK
    except TypeError:
        app_logger.warning("Invalid value type in settings.recent_days_back. "
                           "Using default value of %s", DEFAULT_RECENT_DAYS_AHEAD)
        days_back = DEFAULT_RECENT_DAYS_BACK
    except ValueError:
        app_logger.warning("Invalid value in settings.recent_days_back. "
                           "Using default value of %s", DEFAULT_RECENT_DAYS_AHEAD)
        days_back = DEFAULT_RECENT_DAYS_BACK

    try:
        recent_shows = ww_show.details.retrieve_recent(database_connection,
                                                       include_days_ahead=days_ahead,
                                                       include_days_back=days_back)
        recent_shows.reverse()
    except AttributeError:
        recent_shows = ww_show.details.retrieve_recent(database_connection)
        recent_shows.reverse()

    return render_template("pages/index.html",
                           shows=recent_shows,
                           format_location_name=formatting.format_location_name)

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

#region Sitemap XML Route
@app.route("/sitemap.xml")
def sitemap_xml():
    """Default Sitemap XML"""
    show_years = retrieve_show_years(reverse_order=False)
    sitemap = render_template("sitemaps/sitemap.xml",
                              show_years=show_years)
    return Response(sitemap, mimetype="text/xml")

@app.route("/sitemap-guests.xml")
def sitemap_guest_xml():
    """Supplementary Sitemap XML for Guest Pages"""
    database_connection.reconnect()
    guests = ww_guest.info.retrieve_all(database_connection)
    sitemap = render_template("sitemaps/guests.xml",
                              guests=guests)
    return Response(sitemap, mimetype="text/xml")

@app.route("/sitemap-hosts.xml")
def sitemap_host_xml():
    """Supplementary Sitemap XML for Host Pages"""
    database_connection.reconnect()
    hosts = ww_host.info.retrieve_all(database_connection)
    sitemap = render_template("sitemaps/hosts.xml",
                              hosts=hosts)
    return Response(sitemap, mimetype="text/xml")

@app.route("/sitemap-locations.xml")
def sitemap_location_xml():
    """Supplementary Sitemap XML for Location Pages"""
    database_connection.reconnect()
    locations = ww_location.info.retrieve_all(database_connection,
                                              sort_by_venue=True)
    sitemap = render_template("sitemaps/locations.xml",
                              locations=locations)
    return Response(sitemap, mimetype="text/xml")

@app.route("/sitemap-panelists.xml")
def sitemap_panelist_xml():
    """Supplementary Sitemap XML for Panelist Pages"""
    database_connection.reconnect()
    panelists = ww_panelist.info.retrieve_all(database_connection)
    sitemap = render_template("sitemaps/panelists.xml",
                              panelists=panelists)
    return Response(sitemap, mimetype="text/xml")

@app.route("/sitemap-scorekeepers.xml")
def sitemap_scorekeeper_xml():
    """Supplementary Sitemap XML for Scorekeeper Pages"""
    database_connection.reconnect()
    scorekeepers = ww_scorekeeper.info.retrieve_all(database_connection)
    sitemap = render_template("sitemaps/scorekeepers.xml",
                              scorekeepers=scorekeepers)
    return Response(sitemap, mimetype="text/xml")

@app.route("/sitemap-shows.xml")
def sitemap_shows_xml():
    """Supplementary Sitemap XML for Show Pages"""
    show_dates = retrieve_show_dates(reverse_order=False)
    show_years_months = retrieve_show_years_months(reverse_order=False)
    sitemap = render_template("sitemaps/shows.xml",
                              show_dates=show_dates,
                              show_years_months=show_years_months)
    return Response(sitemap, mimetype="text/xml")

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

    if not guests_list:
        return redirect(url_for("index"))

    return render_template("guests/guests.html", guests=guests_list)

@app.route("/guests/<string:guest>")
def get_guest_details(guest: Text):
    """Presents appearance details for a Not My Job guest"""
    guest_slug = slugify(guest)
    if guest and guest != guest_slug:
        return redirect(url_for("get_guest_details", guest=guest_slug))

    database_connection.reconnect()
    guest_details = ww_guest.details.retrieve_by_slug(guest_slug,
                                                      database_connection)

    if not guest_details:
        return redirect(url_for("get_guests"))

    # Template expects a list of guests(s)
    guests = []
    guests.append(guest_details)
    return render_template("guests/single.html",
                           guest_name=guest_details["name"],
                           guests=guests)

@app.route("/guests/all")
def get_guests_all():
    """Presents appearance details for all Not My Job guests"""
    database_connection.reconnect()
    guests = ww_guest.details.retrieve_all(database_connection)

    if not guests:
        return redirect(url_for("get_guests"))

    return render_template("guests/all.html", guests=guests)

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

    if not hosts_list:
        return redirect(url_for("index"))

    return render_template("hosts/hosts.html", hosts=hosts_list)

@app.route("/hosts/<string:host>")
def get_host_details(host: Text):
    """Presents appearance details for a show host"""
    database_connection.reconnect()
    host_slug = slugify(host)
    if host and host != host_slug:
        return redirect(url_for("get_host_details", host=host_slug))

    host_details = ww_host.details.retrieve_by_slug(host_slug,
                                                    database_connection)

    if not host_details:
        return redirect(url_for("get_hosts"))

    # Template expects a list of hosts(s)
    hosts = []
    hosts.append(host_details)
    return render_template("hosts/single.html",
                           host_name=host_details["name"],
                           hosts=hosts)

@app.route("/hosts/all")
def get_hosts_all():
    """Presents appearance details for all show hosts"""
    database_connection.reconnect()
    hosts = ww_host.details.retrieve_all(database_connection)

    if not hosts:
        return redirect(url_for("get_hosts"))

    return render_template("hosts/all.html", hosts=hosts)

#endregion


#region Location Routes
@app.route("/location")
def get_location():
    """Redirect /location to /locations"""
    return redirect(url_for("get_locations"), code=301)

@app.route("/locations")
def get_locations():
    """Presents a list of locations"""
    database_connection.reconnect()
    location_list = ww_location.info.retrieve_all(database_connection,
                                                  sort_by_venue=True)

    if not location_list:
        return redirect(url_for("index"))

    return render_template("locations/locations.html",
                           locations=location_list,
                           format_location_name=formatting.format_location_name)

@app.route("/locations/<string:location>")
def get_location_details(location: Text):
    """Presents location details and recordings for a location"""
    database_connection.reconnect()
    location_slug = slugify(location)
    if location and location != location_slug:
        return redirect(url_for("get_location_details",
                                location=location_slug))

    location_details = ww_location.details.retrieve_recordings_by_slug(location_slug,
                                                                       database_connection)

    if not location_details:
        return redirect(url_for("get_locations"))

    # Redirect back to /locations for certain placeholder locations
    if "id" in location_details and (location_details["id"] == 3 or
                                     location_details["id"] == 38):
        return redirect(url_for("get_locations"))

    # Template expects a list of location(s)
    locations = []
    locations.append(location_details)
    location_name = formatting.format_location_name(location_details)
    return render_template("locations/single.html",
                           locations=locations,
                           location_name=location_name,
                           format_location_name=formatting.format_location_name)

@app.route("/locations/all")
def get_locations_all():
    """Presents location details and recordings for all locations"""
    database_connection.reconnect()
    locations = ww_location.details.retrieve_all_recordings(database_connection,
                                                            sort_by_venue=True)

    if not locations:
        return redirect(url_for("get_locations"))

    return render_template("locations/all.html",
                           locations=locations,
                           format_location_name=formatting.format_location_name)

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

    if not panelist_list:
        return redirect(url_for("index"))

    return render_template("panelists/panelists.html", panelists=panelist_list)

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

    if not panelist_details:
        return redirect(url_for("get_panelists"))

    # Template expects a list of panelists(s)
    panelists = []
    panelists.append(panelist_details)
    return render_template("panelists/single.html",
                           panelist_name=panelist_details["name"],
                           panelists=panelists)

@app.route("/panelists/all")
def get_panelists_all():
    """Presents statistics and appearance details for all panelists"""
    database_connection.reconnect()
    panelists = ww_panelist.details.retrieve_all(database_connection)

    if not panelists:
        return redirect(url_for("get_panelists"))

    return render_template("panelists/all.html", panelists=panelists)

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
    if not scorekeepers_list:
        return redirect(url_for("index"))

    return render_template("scorekeepers/scorekeepers.html",
                           scorekeepers=scorekeepers_list)

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

    if not scorekeeper_details:
        return redirect(url_for("get_scorekeepers"))

    # Template expects a list of scorekeepers(s)
    scorekeepers = []
    scorekeepers.append(scorekeeper_details)
    return render_template("scorekeepers/single.html",
                           scorekeeper_name=scorekeeper_details["name"],
                           scorekeepers=scorekeepers)

@app.route("/scorekeepers/all")
def get_scorekeepers_all():
    """Presents appearance details for all scorekeepers"""
    database_connection.reconnect()
    scorekeepers = ww_scorekeeper.details.retrieve_all(database_connection)
    if not scorekeepers:
        return redirect(url_for("get_scorekeepers"))

    return render_template("scorekeepers/all.html", scorekeepers=scorekeepers)

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

    if not show_years:
        return redirect(url_for("index"))

    return render_template("shows/shows.html", show_years=show_years)

@app.route("/shows/<int:year>")
def get_shows_year(year: int):
    """Presents a list of available show months for a given year"""
    database_connection.reconnect()
    try:
        date_year = date(year=year, month=1, day=1)
        show_months = ww_show.info.retrieve_months_by_year(show_year=year,
                                                           database_connection=database_connection)

        if not show_months:
            return redirect(url_for("get_shows"))

        months = []
        for month in show_months:
            months.append(date(year=year, month=month, day=1))

        return render_template("shows/year.html",
                               year=date_year,
                               show_months=months)
    except ValueError:
        return redirect(url_for("get_shows"))

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
    try:
        year_month = date(year=year, month=month, day=1)
        show_list = ww_show.details.retrieve_by_year_month(show_year=year,
                                                           show_month=month,
                                                           database_connection=database_connection)
        if not show_list:
            return redirect(url_for("get_shows_year", year=year))

        return render_template("shows/year_month.html",
                               year_month=year_month,
                               shows=show_list,
                               format_location_name=formatting.format_location_name)
    except ValueError:
        return redirect(url_for("get_shows_year", year=year))

@app.route("/shows/<int:year>/<int:month>/<int:day>")
def get_show_year_month_day(year: int, month: int, day: int):
    """Presents show details for a given year, month and day"""
    database_connection.reconnect()
    try:
        show_date = date(year=year, month=month, day=day)
        details = ww_show.details.retrieve_by_date(show_year=year,
                                                   show_month=month,
                                                   show_day=day,
                                                   database_connection=database_connection)
        if not details:
            return redirect(url_for("get_shows_year_month",
                                    year=year,
                                    month=month))

        # Template expects a list of show(s)
        show_list = []
        show_list.append(details)
        return render_template("shows/single.html",
                               show_date=show_date,
                               shows=show_list,
                               format_location_name=formatting.format_location_name)
    except ValueError:
        return redirect(url_for("get_shows"))

@app.route("/shows/<int:year>/all")
def get_shows_year_all(year: int):
    """Presents details for all shows available for a given year"""
    database_connection.reconnect()
    shows_list = ww_show.details.retrieve_by_year(show_year=year,
                                                  database_connection=database_connection)
    if not shows_list:
        return redirect(url_for("get_shows_year", year=year))

    return render_template("shows/year_all.html",
                           year=year,
                           shows=shows_list,
                           format_location_name=formatting.format_location_name)

@app.route("/shows/all")
def get_shows_all():
    """Presents details for all shows across all available years"""
    database_connection.reconnect()
    show_years = retrieve_show_years(reverse_order=False)

    if not show_years:
        return redirect(url_for("get_shows"))

    show_by_years = OrderedDict()
    for year in show_years:
        shows = ww_show.details.retrieve_by_year(show_year=year,
                                                 database_connection=database_connection)
        show_by_years[year] = shows

    return render_template("shows/all.html",
                           show_years=show_years,
                           shows=show_by_years,
                           format_location_name=formatting.format_location_name)

@app.route("/shows/on-this-day")
def get_shows_on_this_day():
    """Presents details for shows that have aired on this day"""
    database_connection.reconnect()
    show_ids = on_this_day.retrieve_on_this_day_show_ids(database_connection)

    show_list = []
    for show_id in show_ids:
        show = ww_show.details.retrieve_by_id(show_id=show_id,
                                              database_connection=database_connection)

        if show:
            show_list.append(show)

    return render_template("shows/on_this_day.html",
                           shows=show_list,
                           format_location_name=formatting.format_location_name)

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
    database_connection.reconnect()
    show_date_object = utility.date_string_to_date(date_string=show_date)

    if not show_date_object:
        return redirect(url_for("index"))

    if ww_show.utility.date_exists(show_year=show_date_object.year,
                                   show_month=show_date_object.month,
                                   show_day=show_date_object.day,
                                   database_connection=database_connection):
        current_url_prefix = "https://www.npr.org/programs/wait-wait-dont-tell-me/archive?date="
        legacy_url_prefix = "https://legacy.npr.org/programs/waitwait/archrndwn"
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
app_time_zone = config["settings"]["app_time_zone"]
time_zone_name = config["settings"]["time_zone"]
app.jinja_env.globals["app_version"] = APP_VERSION
app.jinja_env.globals["libwwdtm_version"] = WWDTM_VERSION
app.jinja_env.globals["current_date"] = date.today()
app.jinja_env.globals["date_string_to_date"] = utility.date_string_to_date
app.jinja_env.globals["ga_property_code"] = config["settings"]["ga_property_code"]
app.jinja_env.globals["current_year"] = utility.current_year
app.jinja_env.globals["rank_map"] = dicts.PANELIST_RANKS
app.jinja_env.globals["time_zone"] = app_time_zone
app.jinja_env.globals["rendered_at"] = utility.generate_date_time_stamp

app.jinja_env.globals["api_url"] = config["settings"]["api_url"]
app.jinja_env.globals["blog_url"] = config["settings"]["blog_url"]
app.jinja_env.globals["graphs_url"] = config["settings"]["graphs_url"]
app.jinja_env.globals["reports_url"] = config["settings"]["reports_url"]
app.jinja_env.globals["site_url"] = config["settings"]["site_url"]

database_connection = mysql.connector.connect(**config["database"])
database_connection.autocommit = True

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port="9248")

#endregion
