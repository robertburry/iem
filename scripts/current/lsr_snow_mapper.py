"""Create an analysis of LSR snowfall reports"""
import tempfile
import os
import subprocess

import requests
from pyiem.util import logger, utc, exponential_backoff

LOG = logger()


def do(url, fn):
    """Do the work."""
    res = exponential_backoff(requests.get, url, timeout=60)
    if res is None:
        LOG.info("%s failure", url)
        return
    if res.status_code != 200:
        LOG.info("%s resulted in %s", url, res.status_code)
        return
    with tempfile.NamedTemporaryFile(delete=False) as tmpfd:
        tmpfd.write(res.content)
    pqstr = f"plot c {utc():%Y%m%d%H%M} {fn} bogus{utc().second} png"
    subprocess.call(f"pqinsert -i -p '{pqstr}' {tmpfd.name}", shell=True)
    os.unlink(tmpfd.name)


def main():
    """Go Main Go."""
    url = (
        "http://iem.local/plotting/auto/plot/207/t:state::csector:IA"
        "::p:both::hours:12::sz:25.png"
    )
    do(url, "lsr_snowfall.png")

    url = (
        "http://iem.local/plotting/auto/plot/207/t:state::csector:IA"
        "::p:contour::hours:12::sz:25.png"
    )
    do(url, "lsr_snowfall_nv.png")

    # -----------------
    url = (
        "http://iem.local/plotting/auto/plot/207/t:state::csector:midwest"
        "::p:contour::hours:12::sz:25.png"
    )
    do(url, "mw_lsr_snowfall.png")


if __name__ == "__main__":
    main()
