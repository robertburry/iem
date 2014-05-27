<?php
/*
 * My logic defines a URL
 */
$url = "/GIS/radmap.php?";

if ($isarchive){
  	/* Set us ahead to GMT and then back into the archive */
  	$ts = $basets + $tzoff - ($imgi * 60 * $interval );
} else {
  $ts = filemtime("/home/ldm/data/gis/images/4326/USCOMP/n0r_".$imgi.".png") - ($imgi * 300);
  $radfile = "/home/ldm/data/gis/images/4326/USCOMP/n0r_".$imgi.".tif";
}
$url .= sprintf("ts=%s&width=%s&height=%s&", date("YmdHi", $ts), $width, $height);


if (isset($x0)) {
	$url .= sprintf("bbox=%.3f,%.3f,%.3f,%.3f&", $x0, $y0, $x1, $y1);
} else {
	$lpad = $zoom / 100.0;
	$url .= sprintf("bbox=%.3f,%.3f,%.3f,%.3f&", 
			$lon0 - $lpad, $lat0 - $lpad,
			$lon0 + $lpad, $lat0 + $lpad);
	$x0 = $lon0 - $lpad;
	$y0 = $lat0 - $lpad;
	$x1 = $lon0 + $lpad;
	$y1 = $lat0 + $lpad;
}

if (in_array("goes_east1V", $layers)) {
	$url .= "layers[]=goes&goes_sector=EAST&goes_product=VIS&";
}
if (in_array("goes_west1V", $layers)) {
	$url .= "layers[]=goes&goes_sector=WEST&goes_product=VIS&";
}

if (in_array("goes_west04I4", $layers)) {
	$url .= "layers[]=goes&goes_sector=WEST&goes_product=IR&";
}
if (in_array("goes_east04I4", $layers)) {
	$url .= "layers[]=goes&goes_sector=EAST&goes_product=IR&";
}

if ( in_array("interstates", $layers) ){
	$url .= "layers[]=interstates&";
}
if ( in_array("usdm", $layers) ){
	$url .= "layers[]=usdm&";
}
if ( in_array("uscounties", $layers) ){
	$url .= "layers[]=uscounties&";
}
if ( in_array("cwas", $layers) ){
	$url .= "layers[]=cwas&";
}
if ( in_array("watches", $layers) ){
	$url .= "layers[]=watches&";
}
if ( in_array("nexrad", $layers) ){
	$url .= "layers[]=nexrad&";
}

if ($warngeo == "both" or $warngeo == "county")
{
	$url .= "layers[]=cbw&";	
}
if ($warngeo == "both")
{
	$url .= "layers[]=cbw&";	
}
	
if ($warngeo == "sbw")
{
	$url .= "layers[]=sbw&";	
}


$lsr_etime = $ts + ($lsrwindow * 60);
$url .= sprintf("layers[]=lsrs&ts2=%s", date("YmdHi", $lsr_etime));

?>
