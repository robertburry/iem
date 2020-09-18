"""Ingest the files kindly sent to me by poker"""
import glob
import re
import datetime
import subprocess
import os

import pytz
from pyiem.util import noaaport_text, get_dbconn
from pyiem.nws.product import TextProduct

BAD_CHARS = r"[^\n\r\001\003a-zA-Z0-9:\(\)\%\.,\s\*\-\?\|/><&$=\+\@]"
DEBUG = False
PGCONN = get_dbconn("afos")
XREF_SOURCE = {
    "KABE": "KPHI",
    "KABI": "KSJT",
    "KACT": "KFWD",
    "KACY": "KPHI",
    "KAEL": "KMPX",
    "KAGS": "KCAE",
    "KAHN": "KFFC",
    "KAIA": "KCYS",
    "KAID": "KIND",
    "KALB": "KALY",
    "KALO": "KDMX",
    "KALS": "KPUB",
    "KALW": "KPDT",
    "KANW": "KLBF",
    "KAPN": "KAPX",
    "KARB": "KDTX",
    "KAST": "KPQR",
    "KATL": "KFFC",
    "KAUB": "KBMX",
    "KAUO": "KBMX",
    "KAUS": "KEWX",
    "KAVL": "KGSP",
    "KAVP": "KBGM",
    "KAYS": "KJAX",
    "KBAK": "KIND",
    "KBBW": "KLBF",
    "KBDL": "KBOX",
    "KBDR": "KOKX",
    "KBFF": "KCYS",
    "KBFI": "KSEW",
    "KBFL": "KHNX",
    "KBHM": "KBMX",
    "KBIE": "KOAX",
    "KBIH": "KVEF",
    "KBIL": "KBYZ",
    "KBIX": "KLIX",
    "KBKW": "KRLX",
    "KBLU": "KSTO",
    "KBNA": "KOHX",
    "KBNO": "KBOI",
    "KBOS": "KBOX",
    "KBPT": "KLCH",
    "KBRL": "KDVN",
    "KBTM": "KMSO",
    "KBTR": "KLIX",
    "KBVE": "KLIX",
    "KBWI": "KLWX",
    "KCAK": "KCLE",
    "KCDR": "KCYS",
    "KCEC": "KEKA",
    "KCFV": "KICT",
    "KCGI": "KPAH",
    "KCHA": "KMRX",
    "KCHH": "KBOX",
    "KCHI": "KLOT",
    "KCIC": "KSTO",
    "KCID": "KDVN",
    "KCIR": "KPAH",
    "KCKL": "KBMX",
    "KCLL": "KHGX",
    "KCLT": "KGSP",
    "KCMH": "KILN",
    "KCNK": "KTOP",
    "KCNU": "KICT",
    "KCON": "KGYX",
    "KCOS": "KPUB",
    "KCOU": "KLSX",
    "KCPR": "KRIW",
    "KCRW": "KRLX",
    "KCSG": "KFFC",
    "KCSM": "KOUN",
    "KCVG": "KILN",
    "KCZD": "KGID",
    "KDAB": "KMLB",
    "KDAY": "KILN",
    "KDBQ": "KDVN",
    "KDCA": "KLWX",
    "KDEN": "KBOU",
    "KDFW": "KFWD",
    "KDRA": "KVEF",
    "KDRT": "KEWX",
    "KDSM": "KDMX",
    "KDTL": "KFGF",
    "KDTW": "KDTX",
    "KEAR": "KGID",
    "KEAT": "KOTX",
    "KEAU": "KMPX",
    "KEDW": "KHNX",
    "KEEW": "KGRB",
    "KEKN": "KRLX",
    "KEKO": "KLKN",
    "KELO": "KDLH",
    "KELP": "KEPZ",
    "KELY": "KLKN",
    "KEMP": "KTOP",
    "KEND": "KOUN",
    "KENW": "KMKX",
    "KERI": "KCLE",
    "KESC": "KMQT",
    "KESF": "KLCH",
    "KEUG": "KPQR",
    "KEVV": "KPAH",
    "KEWR": "KOKX",
    "KEYW": "KKEY",
    "KFAR": "KFGF",
    "KFAT": "KHNX",
    "KFBL": "KMPX",
    "KFFM": "KFGF",
    "KFLG": "KFGZ",
    "KFMY": "KTBW",
    "KFNB": "KOAX",
    "KFNT": "KDTX",
    "KFOE": "KTOP",
    "KFRI": "KTOP",
    "KFRM": "KMPX",
    "KFSI": "KOUN",
    "KFSM": "KLZK",
    "KFTW": "KFWD",
    "KFWA": "KIWX",
    "KGCK": "KDDC",
    "KGEG": "KOTX",
    "KGGG": "KSHV",
    "KGLS": "KHGX",
    "KGPZ": "KDLH",
    "KGRI": "KGID",
    "KGSO": "KRAH",
    "KGTF": "KTFX",
    "KGVW": "KEAX",
    "KHAT": "KILM",
    "KHCO": "KFGF",
    "KHDO": "KEWX",
    "KHFD": "KBOX",
    "KHLC": "KGLD",
    "KHLN": "KTFX",
    "KHMS": "KPDT",
    "KHON": "KFSD",
    "KHOU": "KHGX",
    "KHSI": "KGID",
    "KHSV": "KHUN",
    "KHTL": "KAPX",
    "KHTS": "KRLX",
    "KHUT": "KICT",
    "KHVN": "KOKX",
    "KHVR": "KTFX",
    "KIAB": "KICT",
    "KIAD": "KLWX",
    "KIAH": "KHGX",
    "KILG": "KPHI",
    "KIML": "KLBF",
    "KINL": "KDLH",
    "KINT": "KRAH",
    "KINW": "KFGZ",
    "KIPT": "KCTP",
    "KISN": "KBIS",
    "KIXD": "KEAX",
    "KJEF": "KLSX",
    "KJFK": "KOKX",
    "KJLN": "KSGF",
    "KLAA": "KPUB",
    "KLAF": "KIND",
    "KLAN": "KGRR",
    "KLAS": "KVEF",
    "KLAX": "KLOX",
    "KLBB": "KLUB",
    "KLEX": "KLMK",
    "KLGA": "KOKX",
    "KLGB": "KLOX",
    "KLIC": "KBOU",
    "KLIT": "KLZK",
    "KLMT": "KMFR",
    "KLND": "KRIW",
    "KLNK": "KOAX",
    "KLSE": "KARX",
    "KLWC": "KTOP",
    "KLWS": "KOTX",
    "KLXV": "KPUB",
    "KLYH": "KRNK",
    "KMAI": "KTAE",
    "KMCI": "KEAX",
    "KMCK": "KGLD",
    "KMCN": "KFFC",
    "KMCO": "KMLB",
    "KMCW": "KDMX",
    "KMCX": "KIND",
    "KMEI": "KJAN",
    "KMEM": "KMEG",
    "KMFD": "KCLE",
    "KMGM": "KBMX",
    "KMHK": "KTOP",
    "KMIA": "KMFL",
    "KMKC": "KWNS",
    "KMKE": "KMKX",
    "KMKG": "KGRR",
    "KMLI": "KDVN",
    "KMML": "KFSD",
    "KMMO": "KLOT",
    "KMOD": "KSTO",
    "KMSN": "KMKX",
    "KMSP": "KMPX",
    "KMSY": "KLIX",
    "KMTJ": "KGJT",
    "KMYF": "KSGX",
    "KNEW": "KLIX",
    "KNHK": "KLWX",
    "KNHZ": "KGYX",
    "KNKX": "KSGX",
    "KNQA": "KMEG",
    "KNYC": "KOKX",
    "KOAK": "KMTR",
    "KODX": "KGID",
    "KOFF": "KOAX",
    "KOFK": "KOAX",
    "KOJC": "KEAX",
    "KOKC": "KOUN",
    "KOLM": "KSEW",
    "KOLU": "KOAX",
    "KOMA": "KOAX",
    "KONL": "KLBF",
    "KORD": "KLOT",
    "KORF": "KAKQ",
    "KORH": "KBOX",
    "KOTM": "KDMX",
    "KOVE": "KSTO",
    "KPBI": "KMFL",
    "KPDX": "KPQR",
    "KPHL": "KPHI",
    "KPHX": "KPSR",
    "KPIA": "KILX",
    "KPIT": "KPBZ",
    "KPKD": "KFGF",
    "KPMD": "KLOX",
    "KPNS": "KMOB",
    "KPSP": "KSGX",
    "KPTT": "KDDC",
    "KPVD": "KBOX",
    "KPWK": "KLOT",
    "KPWM": "KGYX",
    "KPZQ": "KAPX",
    "KRAL": "KSGX",
    "KRAP": "KUNR",
    "KRBL": "KSTO",
    "KRBO": "KCRP",
    "KRDD": "KSTO",
    "KRDM": "KPDT",
    "KRDU": "KRAH",
    "KRFD": "KLOT",
    "KRIC": "KAKQ",
    "KRIV": "KSGX",
    "KRKS": "KRIW",
    "KRME": "KBGM",
    "KRMG": "KFFC",
    "KRNO": "KREV",
    "KROA": "KRNK",
    "KROC": "KBUF",
    "KROW": "KABQ",
    "KRPH": "KFWD",
    "KRSL": "KICT",
    "KRST": "KARX",
    "KRTN": "KABQ",
    "KRWF": "KMPX",
    "KRWL": "KCYS",
    "KRZL": "KLOT",
    "KSAC": "KSTO",
    "KSAD": "KTWC",
    "KSAF": "KABQ",
    "KSAN": "KSGX",
    "KSAT": "KEWX",
    "KSAV": "KCHS",
    "KSAW": "KMQT",
    "KSBA": "KLOX",
    "KSBD": "KSGX",
    "KSBN": "KIWX",
    "KSBP": "KLOX",
    "KSBY": "KAKQ",
    "KSCK": "KSTO",
    "KSDB": "KLOX",
    "KSDF": "KLMK",
    "KSDM": "KSGX",
    "KSEA": "KSEW",
    "KSEP": "KFWD",
    "KSEZ": "KFGZ",
    "KSFO": "KSTO",
    "KSHN": "KSEW",
    "KSHR": "KBYZ",
    "KSIL": "KLIX",
    "KSJC": "KMTR",
    "KSKA": "KOTX",
    "KSLE": "KPQR",
    "KSLN": "KICT",
    "KSLO": "KLSX",
    "KSLR": "KFWD",
    "KSMF": "KSTO",
    "KSMO": "KLOX",
    "KSMP": "KPDT",
    "KSMX": "KLOX",
    "KSNA": "KSGX",
    "KSNS": "KMTR",
    "KSNT": "KPIH",
    "KSNY": "KCYS",
    "KSPD": "KPUB",
    "KSPI": "KILX",
    "KSPS": "KOUN",
    "KSRQ": "KTBW",
    "KSSC": "KCAE",
    "KSSI": "KJAX",
    "KSTC": "KMPX",
    "KSTJ": "KEAX",
    "KSTL": "KLSX",
    "KSTS": "KMTR",
    "KSUN": "KPIH",
    "KSUS": "KLSX",
    "KSUU": "KSTO",
    "KSUX": "KFSD",
    "KSWF": "KOKX",
    "KSXT": "KMFR",
    "KSYR": "KBGM",
    "KSZL": "KEAX",
    "KTAD": "KPUB",
    "KTCC": "KABQ",
    "KTCL": "KBMX",
    "KTCM": "KSEW",
    "KTCS": "KEPZ",
    "KTEB": "KOKX",
    "KTLH": "KTAE",
    "KTOL": "KCLE",
    "KTPA": "KTBW",
    "KTPH": "KLKN",
    "KTRI": "KMRX",
    "KTRK": "KREV",
    "KTRM": "KSGX",
    "KTTD": "KPQR",
    "KTTS": "KMLB",
    "KTUL": "KTSA",
    "KTUP": "KMEG",
    "KTUS": "KTWC",
    "KTVC": "KAPX",
    "KTVL": "KREV",
    "KTWF": "KBOI",
    "KTXK": "KSHV",
    "KTYR": "KSHV",
    "KTYS": "KMRX",
    "KUCA": "KBGM",
    "KUIL": "KSEW",
    "KUIN": "KLSX",
    "KUKI": "KEKA",
    "KUMN": "KSGF",
    "KUNO": "KSGF",
    "KUNV": "KCTP",
    "KVBG": "KLOX",
    "KVCT": "KCRP",
    "KVCV": "KSGX",
    "KVIH": "KSGF",
    "KVLD": "KTAE",
    "KVNY": "KLOX",
    "KVPS": "KMOB",
    "KVPZ": "KLOT",
    "KVQN": "KAKQ",
    "KVRB": "KMLB",
    "KVTN": "KLBF",
    "KWAL": "KAKQ",
    "KWJF": "KLOX",
    "KWLD": "KICT",
    "KWMC": "KLKN",
    "KWRI": "KPHI",
    "KWWR": "KOUN",
    "KXMR": "KMLB",
    "KYKM": "KPDT",
    "KYNG": "KCLE",
    "KYUM": "KPSR",
    "KZZV": "KPBZ",
    "PADK": "PAFC",
    "PAED": "PAFC",
    "PAEI": "PAFG",
    "PAJN": "PAJK",
    "PAVD": "PAFC",
    "PAWS": "PAFC",
    "PGUA": "PGUM",
    "PHNL": "PHFO",
    "PHOG": "PHFO",
}


def process(order):
    """ Process this timestamp """
    cursor = PGCONN.cursor()
    ts = datetime.datetime.strptime(order[:6], "%y%m%d").replace(
        tzinfo=pytz.utc
    )
    base = ts - datetime.timedelta(days=2)
    ceiling = ts + datetime.timedelta(days=2)
    subprocess.call("tar -xzf %s" % (order,), shell=True)
    inserts = 0
    deletes = 0
    filesparsed = 0
    bad = 0
    for fn in glob.glob("%s[0-2][0-9].*" % (order[:6],)):
        content = re.sub(
            BAD_CHARS, "", open(fn, "rb").read().decode("ascii", "ignore")
        )
        # Now we are getting closer, lets split by the delimter as we
        # may have multiple products in one file!
        for bulletin in content.split("\001"):
            if bulletin == "":
                continue
            try:
                bulletin = noaaport_text(bulletin)
                prod = TextProduct(bulletin, utcnow=ts, parse_segments=False)
                prod.source = XREF_SOURCE.get(prod.source, prod.source)
            except Exception as exp:
                if DEBUG:
                    o = open("/tmp/bad/%s.txt" % (bad,), "w")
                    o.write(bulletin)
                    o.close()
                    print("Parsing Failure %s" % (exp,))
                bad += 1
                continue
            if prod.valid < base or prod.valid > ceiling:
                # print('Timestamp out of bounds %s %s %s' % (base, prod.valid,
                #                                            ceiling))
                bad += 1
                continue

            table = "products_%s_%s" % (
                prod.valid.year,
                ("0712" if prod.valid.month > 6 else "0106"),
            )
            cursor.execute(
                """
                DELETE from """
                + table
                + """ WHERE pil = %s and
                entered = %s and source = %s and data = %s
            """,
                (prod.afos, prod.valid, prod.source, bulletin),
            )
            deletes += cursor.rowcount
            cursor.execute(
                """
                INSERT into """
                + table
                + """
                (data, pil, entered, source, wmo) values (%s,%s,%s,%s,%s)
            """,
                (bulletin, prod.afos, prod.valid, prod.source, prod.wmo),
            )
            inserts += 1

        os.unlink(fn)
        filesparsed += 1
    print(
        ("%s Files Parsed: %s Inserts: %s Deletes: %s Bad: %s")
        % (order, filesparsed, inserts, deletes, bad)
    )
    cursor.close()
    PGCONN.commit()
    # remove cruft
    for fn in glob.glob("*.wmo"):
        os.unlink(fn)
    os.rename(order, "a" + order)


def main():
    """ Go Main Go """
    os.chdir("/mesonet/tmp/poker")
    for order in glob.glob("??????.DDPLUS.tar.gz"):
        process(order)


if __name__ == "__main__":
    # do something
    main()
