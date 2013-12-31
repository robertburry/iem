<?php

function selectAzosNetwork($network)
{   
    global $rootpath;
    $network = strtoupper($network);
    include_once("$rootpath/include/database.inc.php");
    $dbconn = iemdb('mesosite');
    $rs = pg_exec($dbconn, "SELECT * from networks WHERE id ~* 'ASOS' or id ~* 'AWOS' ORDER by name ASC");
    $s = "<select name=\"network\">\n";
    for ($i=0;$row=@pg_fetch_array($rs,$i);$i++)
    {
       $s .= "<option value=\"". $row["id"] ."\" ";
       if ($row["id"] == $network){ $s .= "SELECTED"; }
       $s .= ">". $row["name"] ."</option>\n";
    }     
    return $s;
} 

function selectNetwork($network)
{
    global $rootpath;
    $network = strtoupper($network);
    include_once("$rootpath/include/database.inc.php");
    $dbconn = iemdb('mesosite');
    $rs = pg_exec($dbconn, "SELECT * from networks ORDER by name ASC");
    $s = "<select name=\"network\">\n";
    for ($i=0;$row=@pg_fetch_array($rs,$i);$i++)
    {
       $s .= "<option value=\"". $row["id"] ."\" ";
       if ($row["id"] == $network){ $s .= "SELECTED"; }
       $s .= ">". $row["name"] ."</option>\n";
    }     
    return $s;
}

/*
 * Generate a select box that allows multiple selections!
 * @param extra is an array of extra values for this box
 */
function networkMultiSelect($network, $selected, $extra=Array(),
		$label="station")
{
    global $rootpath;
    $s = "";
    include_once("$rootpath/include/network.php");
    $nt = new NetworkTable($network);
    $cities = $nt->table;
    $s .= "<select name=\"${label}[]\" size=\"5\" MULTIPLE >\n";
    
    reset($extra);
    while (list($idx,$sid) = each($extra))
    {
    	$s .= "<option value=\"$idx\" ";
    	if ($selected == $idx) { $s .= "SELECTED"; }
    	$s .= ">[$idx] $sid </option>\n";
    }
    
    while (list($sid, $tbl) = each($cities))
    {
        $s .= "<option value=\"$sid\" ";
        if ($selected == $sid) { $s .= "SELECTED"; }
        $s .= ">[$sid] ". $tbl["name"] ."</option>\n";
   }
   $s .= "</select>\n";
   return $s;
}

function networkSelect($network, $selected, $extra=Array(),
		$selectName="station")
{
    global $rootpath;
    $s = "";
    include_once("$rootpath/include/network.php");
    $nt = new NetworkTable($network);
    $cities = $nt->table;
    reset($cities);
    $s .= "<select name=\"$selectName\">\n";
    while (list($sid, $tbl) = each($cities))
    {
        $s .= "<option value=\"$sid\" ";
        if ($selected == $sid) { $s .= "SELECTED"; }
        $s .= ">[$sid] ". $tbl["name"] ."</option>\n";
   }
   while (list($idx,$sid) = each($extra))
   {
        $nt->load_station($sid);
        $tbl = $nt->table[$sid];
        $s .= "<option value=\"$sid\" ";
        if ($selected == $sid) { $s .= "SELECTED"; }
        $s .= ">[$sid] ". $tbl["name"] ."</option>\n";
   }
   $s .= "</select>\n";
   return $s;
}

function networkSelectAuto($network, $selected, $extra=Array())
{
    global $rootpath;
    $network = strtoupper($network);
    $s = "";
    include_once("$rootpath/include/network.php");
    $nt = new NetworkTable($network);
    $cities = $nt->table;
    reset($cities);
    $s .= "<select name=\"station\" onChange=\"this.form.submit()\">\n";
    while (list($sid, $tbl) = each($cities))
    {
        if ($tbl["network"] != $network) continue;
        $s .= "<option value=\"$sid\" ";
        if ($selected == $sid) { $s .= "SELECTED"; }
        $s .= ">[$sid] ". $tbl["name"] ."</option>\n";
   }
   while (list($idx,$sid) = each($extra))
   {
        $nt->load_station($sid);
        $tbl = $nt->table[$sid];
        $s .= "<option value=\"$sid\" ";
        if ($selected == $sid) { $s .= "SELECTED"; }
        $s .= ">[$sid] ". $tbl["name"] ."</option>\n";
   }
   $s .= "</select>\n";
   return $s;
}


function isuagSelect($selected)
{
    global $rootpath;
    $s = "";
    include_once("$rootpath/include/network.php");
    $nt = new NetworkTable("ISUAG");
    $cities = $nt->table;
    reset($cities);
    $s .= '<select name="station">\n';
    while (list($sid, $tbl) = each($cities))
    {
        $s .= "<option value=\"$sid\" ";
        if ($selected == $sid) { $s .= "SELECTED"; }
        $s .= ">". $tbl["name"] ."</option>\n";
   }
   $s .= "</select>\n";
   return $s;
}

function rwisMultiSelect($selected, $size){
global $rootpath;
    include_once("$rootpath/include/network.php");
    $nt = new NetworkTable("IA_RWIS");
    $cities = $nt->table;
  echo "<select name=\"station[]\" size=\"". $size ."\" MULTIPLE>\n";
  echo "<option value=\"_ALL\">Select All</option>\n";
  reset($cities);
  while( list($key, $val) = each($cities) ) {
    if ($val["network"] != "IA_RWIS") continue; 
    echo "<option value=\"". $key ."\"";
    if ($selected == $key){
        echo " SELECTED ";
    }
    echo " >". $val["name"] ." (". $key .")\n";
  }

  echo "</select>\n";
}

?>