"""Hourly temp ranges"""
import calendar

import pytz
import numpy as np
import pandas as pd
from pyiem.plot import figure_axes
from pyiem.util import get_autoplot_context, get_sqlalchemy_conn, utc
from pyiem.exceptions import NoDataFound


def get_description():
    """Return a dict describing how to call this plotter"""
    desc = {}
    desc[
        "description"
    ] = """This plot presents the frequency of a given hourly
    temperature being within the bounds of two temperature thresholds. The
    hour is specified in UTC (Coordinated Universal Time) and observations
    are rounded forward in time such that an observation at :54 after the
    hour is moved to the top of the hour.
    """
    desc["data"] = True
    desc["arguments"] = [
        dict(
            type="zstation",
            name="zstation",
            default="AMW",
            label="Select Station:",
            network="IA_ASOS",
        ),
        dict(type="zhour", name="hour", default=20, label="At Time (UTC):"),
        dict(
            type="int",
            name="t1",
            default=70,
            label="Lower Temperature Bound (inclusive):",
        ),
        dict(
            type="int",
            name="t2",
            default=79,
            label="Upper Temperature Bound (inclusive):",
        ),
    ]
    return desc


def plotter(fdict):
    """Go"""
    ctx = get_autoplot_context(fdict, get_description())
    station = ctx["zstation"]
    hour = ctx["hour"]
    t1 = ctx["t1"]
    t2 = ctx["t2"]
    with get_sqlalchemy_conn("asos") as conn:
        df = pd.read_sql(
            """
        WITH obs as (
            SELECT (valid + '10 minutes'::interval) at time zone 'UTC' as vld,
            round(tmpf::numeric, 0) as tmp from alldata
            WHERE station = %s and report_type = 3 and
            extract(hour from
                (valid + '10 minutes'::interval) at time zone 'UTC') = %s
            and tmpf is not null
        )
        SELECT extract(month from vld) as month,
        sum(case when tmp >= %s and tmp <= %s then 1 else 0 end)::int as hits,
        sum(case when tmp > %s then 1 else 0 end) as above,
        sum(case when tmp < %s then 1 else 0 end) as below,
        count(*) from obs GROUP by month ORDER by month ASC
        """,
            conn,
            params=(station, hour, t1, t2, t2, t1),
            index_col="month",
        )
    if df.empty:
        raise NoDataFound("No Data Found.")
    df["freq"] = df["hits"] / df["count"] * 100.0
    df["above_freq"] = df["above"] / df["count"] * 100.0
    df["below_freq"] = df["below"] / df["count"] * 100.0
    ut = utc(2000, 1, 1, hour, 0)
    localt = ut.astimezone(pytz.timezone(ctx["_nt"].sts[station]["tzname"]))
    title = (
        f"{ctx['_sname']}\nFrequency of {hour} UTC ({localt:%-I %p} LST) "
        rf"Temp between {t1}$^\circ$F and {t2}$^\circ$F"
    )
    (fig, ax) = figure_axes(title=title, apctx=ctx)
    ax.scatter(
        df.index.values,
        df["below_freq"],
        marker="s",
        s=40,
        label=f"Below {t1}",
        color="b",
        zorder=3,
    )
    bars = ax.bar(
        np.arange(1, 13),
        df["freq"],
        fc="tan",
        label=f"{t1} - {t2}",
        zorder=2,
        align="center",
    )
    ax.scatter(
        df.index.values,
        df["above_freq"],
        marker="s",
        s=40,
        label=f"Above {t2}",
        color="r",
        zorder=3,
    )
    for i, _bar in enumerate(bars):
        value = df.loc[i + 1, "hits"]
        label = f"{_bar.get_height():.1f}%"
        if value == 0:
            label = "None"
        ax.text(
            i + 1,
            _bar.get_height() + 3,
            label,
            ha="center",
            fontsize=12,
            zorder=4,
        )
    ax.set_xticks(range(0, 13))
    ax.set_xticklabels(calendar.month_abbr)
    ax.grid(True)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_ylabel("Frequency [%]")
    ax.set_xlim(0.5, 12.5)
    ax.legend(loc=(0.05, -0.14), ncol=3, fontsize=14)
    pos = ax.get_position()
    ax.set_position([pos.x0, pos.y0 + 0.07, pos.width, pos.height * 0.93])
    return fig, df


if __name__ == "__main__":
    plotter({})
