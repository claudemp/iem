var htmlInterface = ['<div class="panel panel-default">',
  '<div class="panel-heading">',
    '<h3 class="panel-title">Select Widget for <span id="iemss-network"></span> Network</h3>',
  '</div>',
  '<div class="panel-body">',
'<div class="row">',
	'<div class="col-sm-6">',


'<label for="stations_in">Available Stations:</label>',
'<select multiple id="stations_in" class="form-control">',
'</select>',
'<div class="form-inline">',
'<div class="form-group">',
    '<input type="text" class="form-control" id="stationfilter" ',
		'placeholder="Enter some text here to filter listing below">',
'</div>',
'<div class="form-group">',
		'<button type="submit" id="stations_add" class="btn btn-default"><i class="glyphicon glyphicon-plus"></i> Add Selected</button>',
		'<button type="submit" id="stations_addall" class="btn btn-default">Add All</button>',
'</div>',
'</div>',
		'</div>',
	'<div class="col-sm-6">',
'<label for="stations_out">Selected Stations:</label>',
'<select multiple id="stations_out" class="form-control" name="stations">',
'</select>',
'<div class="form-group">',
		'<button type="submit" id="stations_del" class="btn btn-default"><i class="glyphicon glyphicon-minus"></i> Remove Selected</button>',
		'<button type="submit" id="stations_delall" class="btn btn-default">Remove All</button>',
'</div>',
	'</div>',
'</div>',
'<br />',
'<div class="row"><div class="col-sm-12">',
		'<div id="map" style="width:100%; height:400px" data-network="IA_DCP"></div>',
'</div></div>',
  '</div><!-- End of panel-body -->',
'</div><!-- End of panel -->'];

var map, selectedFeature, selectControl, geojson, geojsonSource, network;

//http://www.lessanvaezi.com/filter-select-list-options/
jQuery.fn.filterByText = function(textbox, selectSingleMatch) {
	return this.each(function() {
		var select = this;
		var options = [];
		$(select).find('option').each(function() {
			options.push({value: $(this).val(), text: $(this).text()});
		});
		$(select).data('options', options);
		$(textbox).bind('change keyup', function() {
			var options = $(select).empty().scrollTop(0).data('options');
			var search = $.trim($(this).val());
			var regex = new RegExp(search,'gi');

			$.each(options, function(i) {
				var option = options[i];
				if(option.text.match(regex) !== null) {
					$(select).append(
							$('<option>').text(option.text).val(option.value)
					);
				}
			});
			if (selectSingleMatch === true && 
					$(select).children().length === 1) {
				$(select).children().get(0).selected = true;
			}
		});
	});
};



$().ready(function() {  
	
	$("#iemss").append(htmlInterface.join(''));
	network = $("#iemss").attr("data-network");
	$("#iemss-network").html(network);
	
	$('#stations_add').click(function() {  
		return !$('#stations_in option:selected').remove().appendTo('#stations_out');  
	});  
	$('#stations_addall').click(function() {  
		return !$('#stations_in option').remove().appendTo('#stations_out');  
	});  
	$('#stations_delall').click(function() {  
		return !$('#stations_out option').remove().appendTo('#stations_in');  
	});  
	$('#stations_del').click(function() {  
		$('#stations_out option:selected').remove().appendTo('#stations_in');
		$('#stations_out option').each(function(i) {  
			$(this).attr("selected", "selected");  
		});		
		return false;
	});  
	geojsonSource = new ol.source.GeoJSON({
		projection : ol.proj.get('EPSG:3857'),
		url : '/geojson/network.php?network='+network
	});
	geojson = new ol.layer.Vector({
		source : geojsonSource,
		style : function(feature, resolution){
			style = [new ol.style.Style({
				image: new ol.style.Circle({
					fill: new ol.style.Fill({
						color: 'rgba(255,255,255,0.4)'
					}),
					stroke: new ol.style.Stroke({
						color: '#3399CC',
						width: 1.25
					}),
					radius: 5
				}),
				fill: new ol.style.Fill({
					color: 'rgba(255,255,255,0.4)'
				}),
				stroke: new ol.style.Stroke({
					color: '#3399CC',
					width: 1.25
				})

			})];
			return style;
		}
	});

	map = new ol.Map({
		target: 'map',
		layers: [new ol.layer.Tile({
			title: "Global Imagery",
			source: new ol.source.TileWMS({
				url: 'http://maps.opengeo.org/geowebcache/service/wms',
				params: {LAYERS: 'bluemarble', VERSION: '1.1.1'}
			})
		}),
		geojson
		],
		view: new ol.View({
			projection: ol.proj.get('EPSG:3857'),
			center: [-10575351, 5160979],
			zoom: 3
		})
	});

	geojsonSource.on('change', function(e) {
		if (geojsonSource.getState() == 'ready') {
			$.each(geojsonSource.getFeatures(), function (index, feat) {
				$('#stations_in').append($('<option/>', { 
					value: feat.get('sid'),
					text : "["+ feat.get('sid') +"] "+ feat.get('sname') 
				}));
			});
			$("#stations_in").append($("#stations_in option").remove().sort(function(a, b) {
				var at = $(a).text(), bt = $(b).text();
				return (at > bt)?1:((at < bt)?-1:0);
			}));
			$('#stations_in').filterByText($('#stationfilter'), true);
			map.getView().fitExtent(geojsonSource.getExtent(), map.getSize());
		}
	});

	var $newdiv = $("<div>", {id: "popup", style: "width: 250px;"});
	$("#map").append($newdiv);
	var $newdiv2 = $("<div>", {id: "popover-content"});
	$("#map").append($newdiv2);

	element = document.getElementById('popup');

	var popup = new ol.Overlay({
		element: element,
		positioning: 'bottom-center',
		stopEvent: false
	});
	map.addOverlay(popup);

	$(element).popover({
		'placement': 'top',
		'html': true,
		content: function() { return $('#popover-content').html(); }
	});
	// display popup on click
	map.on('click', function(evt) {
		var feature = map.forEachFeatureAtPixel(evt.pixel,
				function(feature, layer) {
			return feature;
		});
		if (feature) {
			var geometry = feature.getGeometry();
			var coord = geometry.getCoordinates();
			var sid = feature.get('sid');
			popup.setPosition(coord);
			var content = "<p>"+ sid
			+" "+ feature.get('sname') +"</p>";
			$('#popover-content').html(content);
			$(element).popover('show');
			$("#stations_in").find("option[value=\""+sid+"\"]").attr("selected", "selected");
		} else {
			$(element).popover('hide');
		}

	});

});  