"""Run hourly to ensure somethings are cached."""
# third party
import requests
from pyiem.util import logger

LOG = logger()
BASEURL = "https://mesonet.agron.iastate.edu/plotting/auto/plot"
URLS = [
    "/97/sector:midwest::var:precip_sum::date1:2022-04-01::cmap:Blues::c:no",
    "/97/sector:midwest::var:precip_depart::date1:2022-04-01::cmap:BrBG::c:no",
    "/97/sector:midwest::var:gdd_sum::date1:2022-04-01::cmap:inferno::c:no",
    "/97/sector:midwest::var:gdd_depart::date1:2022-04-01"
    "::cmap:RdYlBu_r::c:no",
    "/193/csector:midwest::f:168::opt:wpc::scale:7::cmap:Blues",
]


def main():
    """Go Main Go."""
    for url in URLS:
        full = f"{BASEURL}{url}::_cb:1.png"
        LOG.info("Fetching %s", full)
        req = requests.get(full, timeout=120)
        if req.status_code != 200:
            LOG.warning("got status_code %s for %s", req.status_code, full)


if __name__ == "__main__":
    main()
