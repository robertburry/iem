<?php
require_once "../../config/settings.inc.php";
require_once "../../include/mlib.php";
force_https();
require_once "../../include/database.inc.php";
require_once "../../include/myview.php";
require_once "../../include/forms.php";
require_once "setup.php";
require_once "../../include/iemprop.php";
$gmapskey = get_iemprop("google.maps.key");

$alertmsg = "";
if (
    isset($_GET["lat"]) &&
    $_GET["lat"] != "move marker" &&
    floatval($_GET["lat"]) != 0 &&
    floatval($_GET["lat"]) != 1 &&
    floatval($_GET["lat"]) != -1 &&
    floatval($_GET["lon"]) != 0 &&
    floatval($_GET["lon"]) != 1 &&
    floatval($_GET["lon"]) != -1
) {
    // Log the request so to effectively do some DOS protection.
    $pgconn = iemdb("mesosite");
    $rs = pg_prepare(
        $pgconn,
        "INSERT",
        "INSERT into weblog(client_addr, uri, referer, http_status) " .
            "VALUES ($1, $2, $3, $4)"
    );
    pg_execute(
        $pgconn,
        "INSERT",
        array(
            $_SERVER["REMOTE_ADDR"],
            "/sites/site.php?network={$network}&station={$station}",
            $_SERVER["HTTP_REFERER"],
            404
        )
    );
    pg_close($pgconn);

    $newlat = floatval($_GET["lat"]);
    $newlon = floatval($_GET["lon"]);
    $email = isset($_GET["email"]) ? xssafe($_GET["email"]) : 'n/a';
    $name = isset($_GET["name"]) ? xssafe($_GET["name"]) : "n/a";
    $delta = (
        ($newlat - $cities[$station]["lat"]) ** 2 +
        ($newlon - $cities[$station]["lon"]) ** 2) ** 0.5;
    $msg = <<<EOF
IEM Sites Move Request
======================
> REMOTE_ADDR: {$_SERVER["REMOTE_ADDR"]}
> ID:          {$station}
> NAME:        {$name} OLD: {$cities[$station]["name"]}
> NETWORK:     {$network}
> LON:         {$newlon} OLD: {$cities[$station]["lon"]}
> LAT:         {$newlat} OLD: {$cities[$station]["lat"]}
> EMAIL:       {$email}

https://mesonet.agron.iastate.edu/sites/site.php?network={$network}&station={$station}
EOF;
    if (($delta < 0.5) || (strpos($email, '@') > 0)) {
        mail("akrherz@iastate.edu", "Please move {$station} {$network}", $msg);
    }
    $alertmsg = <<<EOM
<div class="alert alert-danger">Thanks! Your suggested move was submitted for
evaluation.</div>
EOM;
}

$t = new MyView();
$t->title = sprintf("Site Info: %s %s", $station, $cities[$station]["name"]);
$t->headextra = <<<EOF
<script src="https://maps.googleapis.com/maps/api/js?key={$gmapskey}" type="text/javascript"></script>
EOF;
$t->sites_current = "base";

$lat = sprintf("%.5f", $cities[$station]["lat"]);
$lon = sprintf("%.5f", $cities[$station]["lon"]);

function pretty_key($key)
{
    if ($key == "TRACKS_STATION") {
        return "Data tracks station";
    }
    return $key;
}
function pretty_value($key, $value)
{
    if ($key == "TRACKS_STATION") {
        $tokens = explode("|", $value);
        return sprintf(
            '<a href="/sites/site.php?station=%s&network=%s">%s [%s]</a>',
            $tokens[0],
            $tokens[1],
            $tokens[0],
            $tokens[1]
        );
    }
    return $value;
}

$attrtable = "";
if (sizeof($cities[$station]["attributes"]) > 0) {
    $attrtable .= <<<EOM
    <h3>Station Attributes:</h3>
    <p><i>These are key value pairs used by the IEM to do data management.</i></p>
    <table class="table table-condensed table-striped">
    <thead><tr><th>Key / Description</th><th>Value</th></tr></thead>
    <tbody>
EOM;
    foreach ($cities[$station]["attributes"] as $key => $value) {
        $attrtable .= sprintf(
            "<tr><td>%s</td><td>%s</td></tr>",
            pretty_key($key),
            pretty_value($key, $value)
        );
    }
    $attrtable .= "</tbody></table>";
}
$threading = "";
if ((strpos($network, "CLIMATE") > 0) && (substr($station, 2, 1) == "T")) {
    $pgconn = iemdb("mesosite");
    pg_prepare(
        $pgconn,
        "SELECT",
        "SELECT t.id, t.network, t.name, s.begin_date, s.end_date " .
            "from station_threading s " .
            "JOIN stations t on (s.source_iemid = t.iemid) WHERE s.iemid = $1 " .
            "ORDER by s.begin_date ASC"
    );
    $result = pg_execute($pgconn, "SELECT", array($metadata["iemid"]));
    if (pg_numrows($result) > 0) {
        $threading = <<<EOM
<h3>Station Threading:</h3>
<p>This station threads together data from multiple stations to provide a
long term record for the location.</p>
<table class="table table-condensed table-striped">
<thead><tr><th>Station</th><th>Begin Date</th><th>End Date</th></tr></thead>
<tbody>
EOM;
    }
    while ($row = pg_fetch_array($result)) {
        $threading .= sprintf(
            "<tr><td><a href=\"/sites/site.php?station=%s&network=%s\">%s (%s)</a></td><td>%s</td><td>%s</td></tr>",
            $row["id"],
            $row["network"],
            $row["name"],
            $row["id"],
            $row["begin_date"],
            $row["end_date"],
        );
    }
    if (pg_numrows($result) > 0) {
        $threading .= "</tbody></table>";
    }
    pg_close($pgconn);
}

$t->content = <<<EOF

{$alertmsg}

<div class="row">
<div class="col-md-4">

<table class="table table-condensed table-striped">
<tr><th>Station Identifier:</th><td>{$station}</td></tr>
<tr><th>Station Name:</th><td>{$cities[$station]["name"]}</td></tr>
<tr><th>Network:</th><td>{$network}</td></tr>
<tr><th>County:</th><td>{$cities[$station]["county"]}</td></tr>
<tr><th>State:</th><td>{$cities[$station]["state"]}</td></tr>
<tr><th>Latitude:</th><td>{$lat}</td></tr>
<tr><th>Longitude:</th><td>{$lon}</td></tr>
<tr><th>Elevation [m]:</th><td>{$cities[$station]["elevation"]}</td></tr>
<tr><th>Time Zone:</th><td>{$cities[$station]["tzname"]}</td></tr>
</table>

{$attrtable}

{$threading}

<a href="networks.php?station={$station}&amp;network={$network}" class="btn btn-primary"><span class="fa fa-menu-hamburger"></span> View {$network} Network Table</a>

</div>
<div class="col-md-8">

  <div id="mymap" style="height: 400px; width: 100%;"></div>
 <div>
 <strong>Is the location shown for this station wrong?</strong>
 <br />If so, please consider submitting a location submission by moving the marker
 on the map and completing this form below.<br />
    <form name="updatecoords" method="GET">
    <input type="hidden" value="{$network}" name="network">
    <input type="hidden" value="{$station}" name="station">
    New Latitude: <input id="newlat" type="text" size="10" name="lat" placeholder="move marker">
    New Longitude: <input id="newlon" type="text" size="10" name="lon" placeholder="move marker">
    <br />Enter Your Email Address [1]: <input type="text" size="40" name="email" placeholder="optional">
    <br />Better Location Name?: <input type="text" name="name" value="{$cities[$station]["name"]}" />
    <br />[1] Your email address will not be shared nor will you be added to any
    lists. The IEM developer will simply email you back after consideration of
    this request.

    <br /><strong>Note:</strong> If you are looking for a wind rose for a location
    other than this, your only option on this website is to find the nearest station
    with data.
    <br /><input type="submit" value="I am asking the location be updated."></form>
</div>
</div>

<script type="text/javascript">
var map, marker;
function load(){
    var mapOptions = {
            zoom: 15,
            center: new google.maps.LatLng({$lat}, {$lon}),
            mapTypeId: google.maps.MapTypeId.ROADMAP
          };
    map = new google.maps.Map(document.getElementById('mymap'),
              mapOptions);
    marker = new google.maps.Marker({
                    position: mapOptions.center,
                      map: map,
                    draggable: true
                });
    google.maps.event.addListener(marker, 'dragend', function() {
          displayCoordinates(marker.getPosition());
    });
                    
    //callback on when the marker is done moving    		
    function displayCoordinates(pnt) {
        var lat = pnt.lat();
        lat = lat.toFixed(8);
        var lng = pnt.lng();
        lng = lng.toFixed(8);
        $("#newlat").val(lat);
        $("#newlon").val(lng);
    }
}
google.maps.event.addDomListener(window, 'load', load);

</script>
EOF;
$t->render('sites.phtml');
