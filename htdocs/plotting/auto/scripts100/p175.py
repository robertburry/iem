"""snow cover coverage."""
import os
import datetime

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.dates as mdates
from pyiem import iemre
from pyiem.plot import figure_axes
from pyiem.grid.zs import CachingZonalStats
from pyiem.util import (
    get_autoplot_context,
    get_sqlalchemy_conn,
    ncopen,
    convert_value,
)
from pyiem import reference
from pyiem.exceptions import NoDataFound


def get_description():
    """Return a dict describing how to call this plotter"""
    desc = {}
    today = datetime.date.today()
    year = today.year if today.month > 9 else today.year - 1
    desc[
        "description"
    ] = """This chart displays estimated areal coverage of
    snow cover for a single state.  This estimate is based on a 0.125x0.125
    degree analysis of NWS COOP observations.  The date shown would represent
    snow depth reported approximately at 7 AM.
    """
    desc["data"] = True
    desc["arguments"] = [
        dict(
            type="year",
            name="year",
            default=year,
            label="Year of December for Winter Season",
        ),
        dict(
            type="float",
            name="thres",
            default="1.0",
            label="Snow Cover Threshold [inch]",
        ),
        dict(type="state", name="state", default="IA", label="For State"),
    ]
    return desc


def f(st, snowd, metric, stpts):
    """f is for Fancy."""
    v = (
        np.ma.sum(
            np.ma.where(np.ma.logical_and(st > 0, snowd >= metric), 1, 0)
        )
        / float(stpts)
        * 100.0
    )
    return np.nan if v is np.ma.masked else v


def plotter(fdict):
    """Go"""
    ctx = get_autoplot_context(fdict, get_description())
    year = ctx["year"]
    thres = ctx["thres"]
    metric = convert_value(thres, "inch", "millimeter")
    state = ctx["state"][:2]

    sts = datetime.datetime(year, 10, 1, 12)
    ets = datetime.datetime(year + 1, 5, 1, 12)
    rows = []

    with get_sqlalchemy_conn("postgis") as conn:
        states = gpd.read_postgis(
            "SELECT the_geom, state_abbr from states where state_abbr = %s",
            conn,
            params=(state,),
            index_col="state_abbr",
            geom_col="the_geom",
        )

    sidx = iemre.daily_offset(sts)
    ncfn = iemre.get_daily_ncname(sts.year)
    if not os.path.isfile(ncfn):
        raise NoDataFound(f"Data for year {sts.year} not found")
    with ncopen(ncfn) as nc:
        czs = CachingZonalStats(iemre.AFFINE)
        hasdata = np.zeros(
            (nc.dimensions["lat"].size, nc.dimensions["lon"].size)
        )
        czs.gen_stats(hasdata, states["the_geom"])
        for nav in czs.gridnav:
            grid = np.ones((nav.ysz, nav.xsz))
            grid[nav.mask] = 0.0
            jslice = slice(nav.y0, nav.y0 + nav.ysz)
            islice = slice(nav.x0, nav.x0 + nav.xsz)
            hasdata[jslice, islice] = np.where(
                grid > 0, 1, hasdata[jslice, islice]
            )
        st = np.flipud(hasdata)
        stpts = np.sum(np.where(hasdata > 0, 1, 0))

        snowd = nc.variables["snowd_12z"][sidx:, :, :]
    for i in range(snowd.shape[0]):
        rows.append(
            {
                "valid": sts + datetime.timedelta(days=i),
                "coverage": f(st, snowd[i], metric, stpts),
            }
        )

    eidx = iemre.daily_offset(ets)
    ncfn = iemre.get_daily_ncname(ets.year)
    if not os.path.isfile(ncfn):
        raise NoDataFound(f"Data for year {ets.year} not found")
    with ncopen(ncfn) as nc:
        snowd = nc.variables["snowd_12z"][:eidx, :, :]
    for i in range(snowd.shape[0]):
        rows.append(
            {
                "valid": datetime.datetime(ets.year, 1, 1, 12)
                + datetime.timedelta(days=i),
                "coverage": f(st, snowd[i], metric, stpts),
            }
        )
    df = pd.DataFrame(rows)
    df = df[np.isfinite(df["coverage"])]
    title = (
        "IEM Estimated Areal Snow Coverage over "
        f"{reference.state_names[state]}\n"
        f"Percentage of state reporting at least {thres:.2f}in snow "
        f"cover depth {df['valid'].min():%b %-d, %Y} - "
        f"{df['valid'].max():%b %-d %Y}"
    )
    (fig, ax) = figure_axes(title=title, apctx=ctx)
    ax.bar(
        df["valid"].values,
        df["coverage"].values,
        fc="tan",
        ec="tan",
        align="center",
    )

    ax.set_ylabel("Areal Coverage [%]")
    ax.xaxis.set_major_locator(mdates.DayLocator([1, 15]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%-d %b\n%Y"))
    one = datetime.timedelta(days=1)
    ax.set_xlim(df["valid"].min() - one, df["valid"].max() + one)
    ax.set_yticks(range(0, 101, 25))
    ax.grid(True)

    return fig, df


if __name__ == "__main__":
    plotter({})
