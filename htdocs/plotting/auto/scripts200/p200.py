"""SPC Convective Outlook Heatmaps."""
import datetime

import numpy as np
from rasterstats import zonal_stats
from geopandas import read_postgis
from affine import Affine
import pandas as pd
from pyiem.plot.geoplot import MapPlot
from pyiem.plot import get_cmap
from pyiem.util import get_autoplot_context, get_dbconn, utc
from pyiem.exceptions import NoDataFound
from pyiem.reference import LATLON


PDICT5 = {
    "yes": "YES: Draw Counties/Parishes",
    "no": "NO: Do Not Draw Counties/Parishes",
}
ISSUANCE = dict(
    (
        ("1.C.1", "Day 1 Convective @1z"),
        ("1.C.5", "Day 1 Convective @5z"),
        ("1.F.6", "Day 1 Fire Weather @6z"),
        ("1.C.13", "Day 1 Convective @13z"),
        ("1.C.16", "Day 1 Convective @16z"),
        ("1.F.16", "Day 1 Fire Weather @16z"),
        ("1.C.20", "Day 1 Convective @20z"),
        ("1.E.8", "Day 1 Excessive Rainfall @8z"),
        ("1.E.16", "Day 1 Excessive Rainfall @16z"),
        ("1.E.1", "Day 1 Excessive Rainfall @1z"),
        ("2.C.6", "Day 2 Convective @6z"),
        ("2.F.7", "Day 2 Fire Weather @7z"),
        ("2.C.17", "Day 2 Convective @17z"),
        ("2.F.19", "Day 2 Fire Weather @19z"),
        ("2.E.9", "Day 2 Excessive Rainfall @9z"),
        ("3.C.7", "Day 3 Convective @7z"),
        ("3.F.21", "Day 3 Fire Weather @21z"),
        ("3.E.9", "Day 3 Excessive Rainfall @9z"),
        ("4.C.8", "Day 4 Convective @8z"),
        ("5.C.8", "Day 5 Convective @8z"),
        ("6.C.8", "Day 6 Convective @8z"),
        ("7.C.8", "Day 7 Convective @8z"),
        ("8.C.8", "Day 8 Convective @8z"),
    )
)
OUTLOOKS = dict(
    (
        ("ANY SEVERE.0.02", "Any Severe 2% (Day 3+)"),
        ("ANY SEVERE.0.05", "Any Severe 5% (Day 3+)"),
        ("ANY SEVERE.0.15", "Any Severe 15% (Day 3+)"),
        ("ANY SEVERE.0.25", "Any Severe 25% (Day 3+)"),
        ("ANY SEVERE.0.30", "Any Severe 30% (Day 3+)"),
        ("ANY SEVERE.0.35", "Any Severe 35% (Day 3+)"),
        ("ANY SEVERE.0.45", "Any Severe 45% (Day 3+)"),
        ("ANY SEVERE.0.60", "Any Severe 60% (Day 3+)"),
        ("ANY SEVERE.SIGN", "Any Severe Significant (Day 3+)"),
        ("CATEGORICAL.TSTM", "Categorical Thunderstorm Risk (Days 1-3)"),
        ("CATEGORICAL.MRGL", "Categorical Marginal Risk (2015+) (Days 1-3)"),
        ("CATEGORICAL.SLGT", "Categorical Slight Risk (Days 1-3)"),
        ("CATEGORICAL.ENH", "Categorical Enhanced Risk (2015+) (Days 1-3)"),
        ("CATEGORICAL.MDT", "Categorical Moderate Risk (Days 1-3)"),
        ("CATEGORICAL.HIGH", "Categorical High Risk (Days 1-3)"),
        (
            "FIRE WEATHER CATEGORICAL.CRIT",
            "Categorical Critical Fire Wx (Days 1-2)",
        ),
        (
            "FIRE WEATHER CATEGORICAL.EXTM",
            "Categorical Extreme Fire Wx (Days 1-2)",
        ),
        (
            "CRITICAL FIRE WEATHER AREA.0.15",
            "Critical Fire Weather Area 15% (Days3-7)",
        ),
        ("HAIL.0.05", "Hail 5% (Days 1+2)"),
        ("HAIL.0.15", "Hail 15% (Days 1+2)"),
        ("HAIL.0.25", "Hail 25% (Days 1+2)"),
        ("HAIL.0.30", "Hail 30% (Days 1+2)"),
        ("HAIL.0.35", "Hail 35% (Days 1+2)"),
        ("HAIL.0.45", "Hail 45% (Days 1+2)"),
        ("HAIL.0.60", "Hail 60% (Days 1+2)"),
        ("HAIL.SIGN", "Hail Significant (Days 1+2)"),
        ("TORNADO.0.02", "Tornado 2% (Days 1+2)"),
        ("TORNADO.0.05", "Tornado 5% (Days 1+2)"),
        ("TORNADO.0.10", "Tornado 10% (Days 1+2)"),
        ("TORNADO.0.15", "Tornado 15% (Days 1+2)"),
        ("TORNADO.0.25", "Tornado 25% (Days 1+2)"),
        ("TORNADO.0.30", "Tornado 30% (Days 1+2)"),
        ("TORNADO.0.35", "Tornado 35% (Days 1+2)"),
        ("TORNADO.0.45", "Tornado 45% (Days 1+2)"),
        ("TORNADO.0.60", "Tornado 60% (Days 1+2)"),
        ("TORNADO.SIGN", "Tornado Significant (Days 1+2)"),
        ("WIND.0.05", "Wind 5% (Days 1+2)"),
        ("WIND.0.15", "Wind 15% (Days 1+2)"),
        ("WIND.0.25", "Wind 25% (Days 1+2)"),
        ("WIND.0.30", "Wind 30% (Days 1+2)"),
        ("WIND.0.35", "Wind 35% (Days 1+2)"),
        ("WIND.0.45", "Wind 45% (Days 1+2)"),
        ("WIND.0.60", "Wind 60% (Days 1+2)"),
        ("WIND.SIGN", "Wind Significant (Days 1+2)"),
    )
)
PDICT = {"cwa": "Plot by NWS Forecast Office", "state": "Plot by State/Sector"}
PDICT2 = {
    "avg": "Average Number of Days per Year",
    "count": "Total Number of Days",
    "lastyear": "Year of Last Issuance",
}
UNITS = {
    "avg": "days per year",
    "count": "days",
    "lastyear": "year",
}
MDICT = dict(
    [
        ("all", "No Month/Time Limit"),
        ("spring", "Spring (MAM)"),
        ("fall", "Fall (SON)"),
        ("winter", "Winter (DJF)"),
        ("summer", "Summer (JJA)"),
        ("jan", "January"),
        ("feb", "February"),
        ("mar", "March"),
        ("apr", "April"),
        ("may", "May"),
        ("jun", "June"),
        ("jul", "July"),
        ("aug", "August"),
        ("sep", "September"),
        ("oct", "October"),
        ("nov", "November"),
        ("dec", "December"),
    ]
)
griddelta = 0.05
GRIDWEST = -139.2
GRIDEAST = -55.1
GRIDNORTH = 54.51
GRIDSOUTH = 19.47

PRECIP_AFF = Affine(griddelta, 0.0, GRIDWEST, 0.0, griddelta * -1, GRIDNORTH)
YSZ = (GRIDNORTH - GRIDSOUTH) / griddelta
XSZ = (GRIDEAST - GRIDWEST) / griddelta


def proxy(mp):
    """TODO remove once pyiem updates"""
    if hasattr(mp, "panels"):
        return mp.panels[0]
    return mp.ax


def get_description():
    """Return a dict describing how to call this plotter"""
    desc = {}
    desc["data"] = True
    desc["cache"] = 86400
    desc[
        "description"
    ] = """
    This application generates heatmaps of Storm Prediction Center
    convective outlooks.

    <p><strong>Major Caveat</strong>: Due to how the IEM stores the outlook
    geometries, the values presented here are for an outlook level and levels
    higher.  For example, if a location was in a moderate risk and you asked
    this app to total slight risks, the moderate risk would count toward the
    slight risk total.</p>

    <p><i class="fa fa-info"></i> This autoplot currently only considers
    outlooks since 2002.</p>
    """
    desc["arguments"] = [
        dict(
            type="select",
            name="month",
            default="all",
            label="Month Limiter",
            options=MDICT,
        ),
        dict(
            type="select",
            name="p",
            default="1.C.16",
            options=ISSUANCE,
            label="Select SPC Product Issuance",
        ),
        dict(
            type="select",
            name="level",
            default="CATEGORICAL.SLGT",
            options=OUTLOOKS,
            label="Select outlook level:",
        ),
        dict(
            type="select",
            name="t",
            default="state",
            options=PDICT,
            label="Select plot extent type:",
        ),
        dict(
            type="networkselect",
            name="station",
            network="WFO",
            default="DMX",
            label="Select WFO: (ignored if plotting state)",
        ),
        dict(
            type="csector",
            name="csector",
            default="conus",
            label="Select state/sector to plot",
        ),
        dict(
            type="select",
            name="drawc",
            default="no",
            options=PDICT5,
            label="Plot County/Parish borders on maps?",
        ),
        dict(
            type="select",
            name="w",
            default="avg",
            options=PDICT2,
            label="Which metric to plot?",
        ),
        dict(
            optional=True,
            type="date",
            name="edate",
            label="Optionally limit plot to this end date:",
            min="2002/01/01",
            default=utc().strftime("%Y/%m/%d"),
        ),
        dict(type="cmap", name="cmap", default="jet", label="Color Ramp:"),
    ]
    return desc


def plotter(fdict):
    """Go"""
    ctx = get_autoplot_context(fdict, get_description())
    level = ctx["level"]
    station = ctx["station"][:4]
    t = ctx["t"]
    p = ctx["p"]
    month = ctx["month"]

    if month == "all":
        months = range(1, 13)
    elif month == "fall":
        months = [9, 10, 11]
    elif month == "winter":
        months = [12, 1, 2]
    elif month == "spring":
        months = [3, 4, 5]
    elif month == "summer":
        months = [6, 7, 8]
    else:
        ts = datetime.datetime.strptime("2000-" + month + "-01", "%Y-%b-%d")
        # make sure it is length two for the trick below in SQL
        months = [ts.month, 999]

    ones = np.ones((int(YSZ), int(XSZ)))
    data = np.zeros((int(YSZ), int(XSZ)))
    # counts = np.load('counts.npy')
    lons = np.arange(GRIDWEST, GRIDEAST, griddelta)
    lats = np.arange(GRIDSOUTH, GRIDNORTH, griddelta)

    pgconn = get_dbconn("postgis")
    hour = int(p.split(".")[2])
    df = read_postgis(
        """
        select product_issue, issue, expire, geom
        from spc_outlooks where outlook_type = %s and day = %s and
        cycle = %s and threshold = %s and category = %s and
        ST_Intersects(geom, ST_GeomFromEWKT('SRID=4326;POLYGON((%s %s, %s %s,
        %s %s, %s %s, %s %s))'))
        and extract(month from product_issue) in %s
        and product_issue > '2002-01-01' and
        product_issue < %s ORDER by product_issue ASC
    """,
        pgconn,
        params=(
            p.split(".")[1],
            p.split(".")[0],
            hour,
            level.split(".", 1)[1],
            level.split(".")[0],
            GRIDWEST,
            GRIDSOUTH,
            GRIDWEST,
            GRIDNORTH,
            GRIDEAST,
            GRIDNORTH,
            GRIDEAST,
            GRIDSOUTH,
            GRIDWEST,
            GRIDSOUTH,
            tuple(months),
            ctx.get("edate", utc() + datetime.timedelta(days=2)),
        ),
        geom_col="geom",
    )
    if df.empty:
        raise NoDataFound("No results found for query")
    for _, row in df.iterrows():
        zs = zonal_stats(
            row["geom"],
            ones,
            affine=PRECIP_AFF,
            nodata=-1,
            all_touched=True,
            raster_out=True,
        )
        for z in zs:
            aff = z["mini_raster_affine"]
            west = aff.c
            north = aff.f
            raster = np.flipud(z["mini_raster_array"])
            x0 = int((west - GRIDWEST) / griddelta)
            y1 = int((north - GRIDSOUTH) / griddelta)
            dy, dx = np.shape(raster)
            x1 = x0 + dx
            y0 = y1 - dy
            if ctx["w"] == "lastyear":
                data[y0:y1, x0:x1] = np.where(
                    raster.mask, data[y0:y1, x0:x1], row["issue"].year
                )
            else:
                data[y0:y1, x0:x1] += np.where(raster.mask, 0, 1)

    years = (utc() - df["issue"].min()).total_seconds() / 365.25 / 86400.0
    if ctx["w"] == "avg":
        data = data / years
    subtitle = "Found %s events for CONUS between %s and %s" % (
        len(df.index),
        df["issue"].min().strftime("%d %b %Y"),
        df["issue"].max().strftime("%d %b %Y"),
    )
    if t == "cwa":
        sector = "cwa"
        subtitle = "Plotted for %s (%s). %s" % (
            ctx["_nt"].sts[station]["name"],
            station,
            subtitle,
        )
    else:
        sector = "state" if len(ctx["csector"]) == 2 else ctx["csector"]

    mp = MapPlot(
        sector=sector,
        state=ctx["csector"],
        cwa=(station if len(station) == 3 else station[1:]),
        axisbg="white",
        title="%s %s Outlook [%s] of at least %s"
        % (
            "WPC" if p.split(".")[1] == "E" else "SPC",
            ISSUANCE[p],
            month.capitalize(),
            OUTLOOKS[level].split("(")[0].strip(),
        ),
        subtitle=f"{PDICT2[ctx['w']]}, {subtitle}",
        nocaption=True,
        twitter=True,
    )
    # Get the main axes bounds
    if t == "state" and ctx["csector"] == "conus":
        domain = data
        lons, lats = np.meshgrid(lons, lats)
        df2 = pd.DataFrame()
    else:
        (west, east, south, north) = proxy(mp).get_extent(LATLON)
        i0 = int((west - GRIDWEST) / griddelta)
        j0 = int((south - GRIDSOUTH) / griddelta)
        i1 = int((east - GRIDWEST) / griddelta)
        j1 = int((north - GRIDSOUTH) / griddelta)
        jslice = slice(j0, j1)
        islice = slice(i0, i1)
        domain = data[jslice, islice]
        lons, lats = np.meshgrid(lons[islice], lats[jslice])
        df2 = pd.DataFrame(
            {"lat": lats.ravel(), "lon": lons.ravel(), "freq": domain.ravel()}
        )
    if ctx["w"] == "lastyear":
        domain = np.where(domain < 1, np.nan, domain)
        rng = range(int(np.nanmin(domain)), int(np.nanmax(domain)) + 2)
    elif ctx["w"] == "count":
        domain = np.where(domain < 1, np.nan, domain)
        rng = np.unique(np.linspace(1, np.nanmax(domain) + 1, 10, dtype=int))
    else:
        rng = [
            round(x, 2)
            for x in np.linspace(
                max([0.01, np.min(domain) - 0.5]), np.max(domain) + 0.1, 10
            )
        ]

    cmap = get_cmap(ctx["cmap"])
    cmap.set_under("white")
    cmap.set_over("black")
    res = mp.pcolormesh(
        lons,
        lats,
        domain,
        rng,
        cmap=cmap,
        clip_on=False,
        units=UNITS[ctx["w"]],
        extend="neither" if ctx["w"] in ["lastyear", "count"] else "max",
    )
    # Cut down on SVG et al size
    res.set_rasterized(True)
    if ctx["drawc"] == "yes":
        mp.drawcounties()

    return mp.fig, df2


if __name__ == "__main__":
    plotter(dict(level="CATEGORICAL.SLGT"))
