<?php
/*
 * Dump the IEM's processing of Iowa AWOS sites, for a couple of reasons
 * 1) We process the daily precip correctly, whereas WXC does not (last I knew)
 * 2) We get a 5 minute datafed and use it to build more accurate daily totals
 *    not found in the METAR feed.
 */
include "../../config/settings.inc.php";
include "../../include/mlib.php";

function fancy($v, $floor,$ceil, $p){
  if ($v < $floor || $v > $ceil) return "";
  return sprintf("%${p}.1f", $v);
}

$jdata = file_get_contents("http://iem.local/api/1/currents.json?network=AWOS");
$jobj = json_decode($jdata, $assoc=TRUE);

$rwis = fopen('/tmp/wxc_ia_awos.txt', 'w');
fwrite($rwis, "Weather Central 001d0300 Surface Data
  13
   5 Station
  52 CityName
   2 State
   7 Lat
   8 Lon
   2 Day
   4 Hour
   5 AirTemp
   5 AirDewp
   4 Wind Direction Degrees
   4 Wind Direction Text
   4 Wind Speed
   5 Today Precipitation
");
 


$now = time();
while ( list($bogus, $val) = each($jobj["data"]) ) {
  $tdiff = $now - strtotime($val["local_valid"]);
  if ($tdiff > 3600){ continue; }
  if ($val['pday'] < 0){ $val['pday'] = 0; }

  $s = sprintf("%5s %52s %2s %7s %8s %2s %4s %5s %5s %4s %4s %4s %5s\n", $val["station"], 
    $val['name'], 'IA', round($val['lat'],2), 
     round($val['lon'],2),
      date('d', strtotime($val["local_valid"]) + (6*3600) ), date('H', strtotime($val["local_valid"]) + (6*3600)),
     $val['tmpf'], $val['dwpf'],
     $val['drct'], drct2txt($val['drct']), $val['sknt'], 
     $val['pday']); 
  fwrite($rwis, $s);
} // End of while

fclose($rwis);

$pqstr = "data c 000000000000 wxc/wxc_ia_awos.txt bogus txt";
$cmd = sprintf("/home/ldm/bin/pqinsert -p '%s' /tmp/wxc_ia_awos.txt", $pqstr);
system($cmd);
unlink("/tmp/wxc_ia_awos.txt");

?>
