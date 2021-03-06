from urlparse import urlparse
from collections import Counter
from operator import itemgetter
import datetime

import numpy as np
import pandas as pd
import networkx as nx

from bokeh.plotting import figure, show, output_file
from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.models.widgets import Panel, Tabs, Button, DataTable, DateFormatter, TableColumn
from bokeh.models.widgets.layouts import HBox, VBox
from bokeh.charts import Bar
from bokeh.io import vform, vplot


DOMAIN_PLOT_LIMIT = 10
DOMAIN_TABLE_LIMIT = None

ENDING_PLOT_LIMIT = 10
ENDING_TABLE_LIMIT = None

BAR_WIDTH = 0.4


def pages_timeseries(response):
    parsed_dates = pd.Series(pd.to_datetime([x[1] for x in response]).order(),
            name="datetimes")
    hits = pd.Series(range(1, len(parsed_dates) + 1), name="hits")
    dates = pd.concat([hits, parsed_dates], axis=1).set_index("datetimes")
    dates = dates.resample("30S").dropna()
    plot = figure(plot_height=584, x_axis_type="datetime", x_axis_label="Time",
            y_axis_label="Fetched")
    plot.line(x=dates.index, y=dates["hits"])
    return Panel(child=plot, title="Fetched")


def endings_table(source):
    columns = [
            TableColumn(field="x", title="Ending"),
            TableColumn(field="y", title="Count"),
        ]
    table = DataTable(source=source,
            columns=columns, width=400, height=280)
    return table


def endings_plot(source):
    plot = Bar(source.data, values="y", label="x",
            title="Most Common URL Endings by Number", bar_width=BAR_WIDTH,
            height=584, xlabel="Endings", ylabel="Occurences")
    return plot


def endings_dashboard(response):
    urls = [x[0][0] for x in response["pages"]]
    parsed_urls = [urlparse(x).hostname for x in urls]
    endings_counter = Counter([x[x.rfind("."):] for x in parsed_urls]).most_common(ENDING_PLOT_LIMIT)
    xendings = [x[0] for x in endings_counter]
    yendings = [y[1] for y in endings_counter]
    source = ColumnDataSource(data=dict(x=xendings, y=yendings))

    table = VBox(children=[endings_table(source)])
    plot = VBox(children=[endings_plot(source)])
    return components(vplot(HBox(children=[table, plot])))


def domains_dashboard(response, extra_plots=None):
    """
    Domains dashboard plot function. Takes an arguments for extra plots which
    will be added in a tab with the other plots.
    """
    # Parsed Response Data
    urls = [x[0][0] for x in response["pages"]]
    parsed_urls = [urlparse(x).hostname for x in urls]

    # Domain names Bar chart.
    domains_counter = Counter(parsed_urls).most_common(DOMAIN_PLOT_LIMIT)
    xdomains = [x[0] for x in domains_counter]
    ydomains = [y[1] for y in domains_counter]
    source_domains = ColumnDataSource(data=dict(x=xdomains, y=ydomains))

    bar_domains = Bar(source_domains.data, values="y", label="x", title="Most Common Sites by Number",
            bar_width=BAR_WIDTH, height=584, xlabel="Sites",
            ylabel="Occurences")
    panel_domains = Panel(child=bar_domains, title="Sites")

    # Domain Information Table
    table_domains_counter = Counter(parsed_urls).most_common(DOMAIN_TABLE_LIMIT)
    xdomains_table = [x[0] for x in table_domains_counter]
    ydomains_table = [y[1] for y in table_domains_counter]
    source_table_domains = ColumnDataSource(data=dict(x=xdomains_table,
        y=ydomains_table))

    columns_domain = [
            TableColumn(field="x", title="Site Name"),
            TableColumn(field="y", title="Count"),
        ]
    data_table_domain = DataTable(source=source_table_domains, columns=columns_domain, width=400,
            height=280)

    # Add the plots and charts to a vform and organize them with VBox and HBox
    plot_tabs = Tabs(tabs=[panel_domains, extra_plots])

    # Take the plot and table and arrange them in a hbox.
    vbox_tables = VBox(children=[data_table_domain])
    vbox_plots = VBox(children=[plot_tabs])
    hbox_dashboard = HBox(children=[vbox_tables, vbox_plots])
    return components(vplot(hbox_dashboard))
