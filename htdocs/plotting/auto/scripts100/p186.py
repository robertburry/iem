"""USDM Filled Time Series"""
import datetime
import calendar

import numpy as np
import requests
import pandas as pd
from scipy.interpolate import interp1d
from pyiem import util
from pyiem.plot import figure
from pyiem.reference import state_names, state_fips
from pyiem.exceptions import NoDataFound

SERVICE = (
    "https://droughtmonitor.unl.edu"
    "/DmData/DataTables.aspx/ReturnTabularDMAreaPercent_state"
)
COLORS = ["#ffff00", "#fcd37f", "#ffaa00", "#e60000", "#730000"]


def get_description():
    """Return a dict describing how to call this plotter"""
    desc = {}
    desc["data"] = True
    desc[
        "description"
    ] = """This plot shows the weekly change in drought
    monitor intensity expressed in terms of category change over the area
    of the selected state.  For example, an arrow of length one pointing
    up would indicate a one category improvement in drought over the area
    of the state. This
    plot uses a JSON data service provided by the
    <a href="https://droughtmonitor.unl.edu">Drought Monitor</a> website.
    """
    thisyear = datetime.date.today().year
    desc["arguments"] = [
        dict(type="state", name="state", default="IA", label="Select State:"),
        dict(
            type="year",
            name="syear",
            min=2000,
            default=2000,
            label="Start year for plot",
        ),
        dict(
            type="year",
            name="eyear",
            max=thisyear,
            default=thisyear,
            label="End year (inclusive) for plot",
        ),
    ]
    return desc


def plotter(fdict):
    """Go"""
    ctx = util.get_autoplot_context(fdict, get_description())
    state = ctx["state"]
    syear = ctx["syear"]
    eyear = ctx["eyear"]

    fips = ""
    for key, _state in state_fips.items():
        if _state == state:
            fips = key
    payload = {"area": fips, "statstype": "2"}
    headers = {}
    headers["Accept"] = "application/json, text/javascript, */*; q=0.01"
    headers["Content-Type"] = "application/json; charset=UTF-8"
    req = util.exponential_backoff(
        requests.get, SERVICE, payload, headers=headers
    )
    if req is None or req.status_code != 200:
        raise NoDataFound("Drought Web Service failed to deliver data.")
    jdata = req.json()
    if "d" not in jdata:
        raise NoDataFound("Data Not Found.")
    df = pd.DataFrame(jdata["d"])
    df["Date"] = pd.to_datetime(df["mapDate"], format="%m/%d/%Y")
    df = df.sort_values("Date", ascending=True)
    df["x"] = df["Date"] + datetime.timedelta(hours=(3.5 * 24))
    # accounting
    df["score"] = (
        df["D4"] * 5 + df["D3"] * 4 + df["D2"] * 3 + df["D1"] * 2 + df["D0"]
    )
    df["delta"] = df["score"].diff()
    df.iat[0, df.columns.get_loc("delta")] = 0

    fig = figure(apctx=ctx)
    ax = fig.add_axes([0.1, 0.1, 0.87, 0.84])
    for year, gdf in df.groupby(df.Date.dt.year):
        if year < syear or year > eyear:
            continue
        xs = []
        ys = []
        for _, row in gdf.iterrows():
            xs.append(int(row["Date"].strftime("%j")))
            ys.append(year + row["delta"] / 100.0)
        if len(xs) < 4:
            continue
        fcube = interp1d(xs, ys, kind="cubic")
        xnew = np.arange(xs[0], xs[-1])
        yval = np.ones(len(xnew)) * year
        ynew = fcube(xnew)
        ax.fill_between(
            xnew,
            yval,
            ynew,
            where=(ynew < yval),
            facecolor="blue",
            interpolate=True,
        )
        ax.fill_between(
            xnew,
            yval,
            ynew,
            where=(ynew >= yval),
            facecolor="red",
            interpolate=True,
        )

    ax.set_ylim(eyear + 1, syear - 1)
    ax.set_xlim(0, 366)
    ax.set_xlabel(
        "curve height of 1 year is 1 effective drought category "
        f"change over area of {state_names[state]}"
    )
    ax.set_ylabel(f"Year, thru {df.Date.max():%d %b %Y}")
    ax.set_title(
        f"{syear:.0f}-{eyear:.0f} US Drought Monitor Weekly "
        f"Change for {state_names[state]}\n"
        "curve height represents change in intensity + coverage"
    )

    ax.grid(True)
    ax.set_xticks((1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335))
    ax.set_xticklabels(calendar.month_abbr[1:])

    ax.set_yticks(
        np.arange(ax.get_ylim()[0] - 1, ax.get_ylim()[1], -1, dtype="i")
    )
    fig.text(0.02, 0.03, "Blue areas are improving conditions", color="b")
    fig.text(0.4, 0.03, "Red areas are degrading conditions", color="r")

    return fig, df


if __name__ == "__main__":
    plotter({})
