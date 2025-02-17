// TODO print grid
var dragPan;
var olmap; // Openlayers map
var lsrtable; // LSR DataTable
var sbwtable; // SBW DataTable
var n0q; // RADAR Layer
var lsrLayer;
var sbwLayer;
var counties;
var wfoSelect;
var lsrtypefilter;
var sbwtypefilter;
var dateFormat1 = "YYYYMMDDHHmm";
var nexradBaseTime = moment().utc().subtract(moment().minutes() % 5, "minutes");
var realtime = false;
var TABLE_FILTERED_EVENT = "tfe";

// Use momentjs for formatting
$.datetimepicker.setDateFormatter('moment');

// https://datatables.net/plug-ins/api/row().show()
$.fn.dataTable.Api.register('row().show()', function () {
    var page_info = this.table().page.info();
    // Get row index
    var new_row_index = this.index();
    // Row position
    var row_position = this.table()
        .rows({ search: 'applied' })[0]
        .indexOf(new_row_index);
    // Already on right page ?
    if ((row_position >= page_info.start && row_position < page_info.end) || row_position < 0) {
        // Return row object
        return this;
    }
    // Find page number
    var page_to_display = Math.floor(row_position / this.table().page.len());
    // Go to that page
    this.table().page(page_to_display);
    // Return row object
    return this;
});

function parse_href() {
    // Figure out how we were called
    var tokens = window.location.href.split('#');
    if (tokens.length != 2) {
        return;
    }
    var tokens2 = tokens[1].split("/");
    if (tokens2.length < 2) {
        return;
    }
    var wfos = tokens2[0].split(",");
    wfoSelect.val(wfos).trigger("change");
    if (tokens2.length > 2) {
        var sts = moment.utc(tokens2[1], dateFormat1);
        var ets = moment.utc(tokens2[2], dateFormat1);
    }
    else {
        realtime = true;
        $("#realtime").prop('checked', true);
        // Offset timing
        var ets = moment.utc();
        var sts = moment.utc(ets).add(parseInt(tokens2[1]), 'seconds');
    }
    $("#sts").val(sts.local().format("L LT"));
    $("#ets").val(ets.local().format("L LT"));
    updateRADARTimes();
    if (tokens2.length > 3) {
        // We have settings
        applySettings(tokens2[3]);
    }
    loadData();
}
function cronMinute() {
    if (!realtime) return;
    // Compute the delta
    var sts = moment($("#sts").val(), 'L LT').utc();
    var ets = moment($("#ets").val(), 'L LT').utc();
    $("#ets").val(moment().format('L LT'));
    var seconds = ets.diff(sts) / 1000;  // seconds
    $("#sts").val(moment().subtract(seconds, 'seconds').format('L LT'));
    loadData();
}
function getRADARSource(dt) {
    var prod = dt.year() < 2011 ? 'N0R' : 'N0Q';
    return new ol.source.XYZ({
        url: '/cache/tile.py/1.0.0/ridge::USCOMP-' + prod + '-' + dt.utc().format('YMMDDHHmm') + '/{z}/{x}/{y}.png'
    });
}

function make_iem_tms(title, layername, visible, type) {
    return new ol.layer.Tile({
        title: title,
        visible: visible,
        type: type,
        source: new ol.source.XYZ({
            url: '/c/tile.py/1.0.0/' + layername + '/{z}/{x}/{y}.png'
        })
    })
}

var sbwLookup = {
    "TO": 'red',
    "MA": 'purple',
    "FF": 'green',
    "EW": 'green',
    "FA": 'green',
    "FL": 'green',
    "SV": 'yellow',
    "SQ": "#C71585",
    "DS": "#FFE4C4"
}

// Lookup 'table' for styling
var lsrLookup = {
    "0": "icons/tropicalstorm.gif",
    "1": "icons/flood.png",
    "2": "icons/other.png",
    "3": "icons/other.png",
    "4": "icons/other.png",
    "5": "icons/ice.png",
    "6": "icons/cold.png",
    "7": "icons/cold.png",
    "8": "icons/fire.png",
    "9": "icons/other.png",
    "a": "icons/other.png",
    "A": "icons/wind.png",
    "B": "icons/downburst.png",
    "C": "icons/funnelcloud.png",
    "D": "icons/winddamage.png",
    "E": "icons/flood.png",
    "F": "icons/flood.png",
    "v": "icons/flood.png",
    "G": "icons/wind.png",
    "H": "icons/hail.png",
    "I": "icons/hot.png",
    "J": "icons/fog.png",
    "K": "icons/lightning.gif",
    "L": "icons/lightning.gif",
    "M": "icons/wind.png",
    "N": "icons/wind.png",
    "O": "icons/wind.png",
    "P": "icons/other.png",
    "Q": "icons/tropicalstorm.gif",
    "s": "icons/sleet.png",
    "T": "icons/tornado.png",
    "U": "icons/fire.png",
    "V": "icons/avalanche.gif",
    "W": "icons/waterspout.png",
    "X": "icons/funnelcloud.png",
    "x": "icons/debrisflow.png",
    "Z": "icons/blizzard.png"
};

var lsr_context = {
    getText: function (feature) {
        if (feature.attributes['type'] == 'S') {
            return feature.attributes["magnitude"];
        } else if (feature.attributes['type'] == 'R') {
            return feature.attributes["magnitude"];
        }
        return "";
    },
    getExternalGraphic: function (feature) {
        if (feature.attributes['type'] == 'S' ||
            feature.attributes['type'] == 'R') {
            return "";
        }
        return lsrLookup[feature.attributes['type']];
    }
};
var sbwStyle = [new ol.style.Style({
    stroke: new ol.style.Stroke({
        color: '#000',
        width: 4.5
    })
}), new ol.style.Style({
    stroke: new ol.style.Stroke({
        color: '#319FD3',
        width: 3
    })
})
];
var lsrStyle = new ol.style.Style({
    image: new ol.style.Icon({ src: lsrLookup['9'] })
});

var textStyle = new ol.style.Style({
    text: new ol.style.Text({
        font: 'bold 11px "Open Sans", "Arial Unicode MS", "sans-serif"',
        fill: new ol.style.Fill({
            color: 'white'
        }),
        placement: 'point',
        backgroundFill: new ol.style.Fill({
            color: "black"
        }),
        padding: [2, 2, 2, 2]
    })
});
var lsrTextBackgroundColor = {
    'S': 'purple',
    'R': 'blue',
    '5': 'pink'
}

// create vector layer
lsrLayer = new ol.layer.Vector({
    title: "Local Storm Reports",
    source: new ol.source.Vector({
        format: new ol.format.GeoJSON()
    }),
    style: function (feature, resolution) {
        if (feature.hidden === true) {
            return new ol.style.Style();
        }
        var mag = feature.get('magnitude').toString();
        var typ = feature.get('type');
        if (mag != "") {
            if (typ == 'S' || typ == 'R' || typ == '5') {
                textStyle.getText().setText(mag);
                textStyle.getText().getBackgroundFill().setColor(
                    lsrTextBackgroundColor[typ]
                );
                return textStyle;
            }
        }
        var url = lsrLookup[typ];
        if (url) {
            var icon = new ol.style.Icon({
                src: url
            });
            lsrStyle.setImage(icon);
        }
        return lsrStyle;
    }
});
lsrLayer.addEventListener(TABLE_FILTERED_EVENT, function () {
    // Turn all features back on
    lsrLayer.getSource().getFeatures().forEach((feat) => {
        feat.hidden = false;
    });
    // Filter out the map too
    lsrtable.rows({ "search": "removed" }).every(function (idx) {
        var feat = lsrLayer.getSource().getFeatureById(this.data().id);
        feat.hidden = true;
    });
    lsrLayer.changed();
});
lsrLayer.getSource().on('change', function (e) {
    if (lsrLayer.getSource().isEmpty()) {
        return;
    }
    if (lsrLayer.getSource().getState() == 'ready') {
        olmap.getView().fit(
            lsrLayer.getSource().getExtent(),
            {
                size: olmap.getSize(),
                padding: [50, 50, 50, 50]
            }
        );
    }
    lsrtable.rows().remove();
    var data = [];
    lsrLayer.getSource().getFeatures().forEach(function (feat) {
        var props = feat.getProperties();
        props.id = feat.getId();
        data.push(props);
    });
    lsrtable.rows.add(data).draw();

    // Build type filter
    lsrtable.column(7).data().unique().sort().each(function (d, j) {
        lsrtypefilter.append('<option value="' + d + '">' + d + '</option');
    });
});

sbwLayer = new ol.layer.Vector({
    title: "Storm Based Warnings",
    source: new ol.source.Vector({
        format: new ol.format.GeoJSON()
    }),
    visible: true,
    style: function (feature, resolution) {
        if (feature.hidden === true) {
            return new ol.style.Style();
        }
        var color = sbwLookup[feature.get('phenomena')];
        if (color === undefined) return;
        sbwStyle[1].getStroke().setColor(color);
        return sbwStyle;
    }
});
sbwLayer.addEventListener(TABLE_FILTERED_EVENT, function () {
    // Turn all features back on
    sbwLayer.getSource().getFeatures().forEach((feat) => {
        feat.hidden = false;
    });
    // Filter out the map too
    sbwtable.rows({ "search": "removed" }).every(function (idx) {
        var feat = sbwLayer.getSource().getFeatureById(this.data().id);
        feat.hidden = true;
    });
    sbwLayer.changed();
});
sbwLayer.getSource().on('change', function (e) {
    sbwtable.rows().remove();
    var data = [];
    sbwLayer.getSource().getFeatures().forEach(function (feat) {
        var props = feat.getProperties();
        props.id = feat.getId();
        data.push(props);
    });
    sbwtable.rows.add(data).draw();

    // Build type filter
    sbwtable.column(3).data().unique().sort().each(function (d, j) {
        sbwtypefilter.append('<option value="' + iemdata.vtec_phenomena[d] + '">' + iemdata.vtec_phenomena[d] + '</option');
    });

});

function formatLSR(data) {
    // Format what is presented
    return '<div><strong>Source:</strong> ' + data.source +
        ' &nbsp; <strong>UTC Valid:</strong> ' + data.valid +
        '<br /><strong>Remark:</strong> ' + data.remark +
        '</div>';
}

function revisedRandId() {
    return Math.random().toString(36).replace(/[^a-z]+/g, '').substr(2, 10);
}
function lsrHTML(feature) {
    var lines = [];
    var dt = moment.utc(feature.get("valid"));
    var ldt = dt.local().format("M/D LT");
    var z = dt.utc().format("kk:mm")
    lines.push("<strong>Valid:</strong> " + ldt + " (" + z + "Z)");
    var v = feature.get("source");
    if (v !== null) {
        lines.push("<strong>Source:</strong> " + v);
    }
    v = feature.get("typetext");
    if (v !== null) {
        lines.push("<strong>Type:</strong> " + v);
    }
    v = feature.get("magnitude");
    if (v !== null && v != "") {
        var unit = feature.get("unit");
        if (unit === null) {
            unit = "";
        }
        lines.push("<strong>Magnitude:</strong> " + v + " " + unit);
    }
    v = feature.get("remark");
    if (v !== null) {
        lines.push("<strong>Remark:</strong> " + v);
    }
    return lines.join("<br />");
}

function formatSBW(feature) {
    var lines = [];
    var ph = feature.get("phenomena");
    var pph = ph in iemdata.vtec_phenomena ? iemdata.vtec_phenomena[ph] : ph;
    var s = feature.get("significance");
    var ss = s in iemdata.vtec_significance ? iemdata.vtec_significance[s] : s;
    lines.push("<strong>" + pph + " " + ss + "</strong>");
    var issue = moment.utc(feature.get("issue"));
    var expire = moment.utc(feature.get("expire"));
    var ldt = issue.local().format("M/D LT");
    var z = issue.utc().format("kk:mm")
    lines.push("<strong>Issued:</strong> " + ldt + " (" + z + "Z)");
    ldt = expire.local().format("M/D LT");
    z = expire.utc().format("kk:mm")
    lines.push("<strong>Expired:</strong> " + ldt + " (" + z + "Z)");
    lines.push("<strong>More Details:</strong> <a href='" + feature.get("href") + "' target='_blank'>VTEC Browser</a>");
    return lines.join("<br />");
}

function handleSBWClick(feature) {
    var divid = revisedRandId();
    var div = document.createElement("div");
    var title = feature.get("wfo") + " " + feature.get("phenomena") +
        "." + feature.get("significance") + " #" + feature.get("eventid");
    div.innerHTML = '<div class="panel panel-primary panel-popup" id="' + divid + '">' +
        '<div class="panel-heading">' + title +
        ' &nbsp; <button type="button" class="close" ' +
        'data-target="#' + divid + '" data-dismiss="alert"> ' +
        '<span aria-hidden="true">&times;</span>' +
        '<span class="sr-only">Close</span></button></div>' +
        '<div class="panel-body">' + formatSBW(feature) + '</div>' +
        '</div>';
    var coordinates = feature.getGeometry().getFirstCoordinate();
    var marker = new ol.Overlay({
        position: coordinates,
        positioning: 'center-center',
        element: div,
        stopEvent: false,
        dragging: false
    });
    olmap.addOverlay(marker);
    div.addEventListener('mousedown', function (evt) {
        dragPan.setActive(false);
        marker.set('dragging', true);
    });
    olmap.on('pointermove', function (evt) {
        if (marker.get('dragging') === true) {
            marker.setPosition(evt.coordinate);
        }
    });
    olmap.on('pointerup', function (evt) {
        if (marker.get('dragging') === true) {
            dragPan.setActive(true);
            marker.set('dragging', false);
        }
    });
    var id = feature.getId();
    sbwtable.rows().deselect();
    sbwtable.row(
        sbwtable.rows(function (idx, data, node) {
            if (data["id"] === id) {
                sbwtable.row(idx).select();
                return true;
            }
            return false;
        })
    ).show().draw(false);

}
function initUI() {
    // Generate UI components of the page
    var handle = $("#radartime");
    $("#timeslider").slider({
        min: 0,
        max: 100,
        create: function () {
            handle.text(nexradBaseTime.local().format("L LT"));
        },
        slide: function (event, ui) {
            var dt = moment(nexradBaseTime);
            dt.add(ui.value * 5, 'minutes');
            handle.text(dt.local().format("L LT"));
        },
        change: function (event, ui) {
            var dt = moment(nexradBaseTime);
            dt.add(ui.value * 5, 'minutes');
            n0q.setSource(getRADARSource(dt));
            handle.text(dt.local().format("L LT"));
        }
    });
    n0q = new ol.layer.Tile({
        title: 'NEXRAD Base Reflectivity',
        visible: true,
        source: getRADARSource(nexradBaseTime)
    });
    lsrtypefilter = $("#lsrtypefilter").select2({
        placeholder: "Filter LSRs by Event Type",
        width: 300,
        multiple: true
    });
    lsrtypefilter.on("change", function () {
        var vals = $(this).val();
        var val = vals ? vals.join("|") : null;
        lsrtable.column(7).search(val ? '^' + val + '$' : '', true, false).draw();
    });
    sbwtypefilter = $("#sbwtypefilter").select2({
        placeholder: "Filter SBWs by Event Type",
        width: 300,
        multiple: true
    });
    sbwtypefilter.on("change", function () {
        var vals = $(this).val();
        var val = vals ? vals.join("|") : null;
        sbwtable.column(3).search(val ? '^' + val + '$' : '', true, false).draw();
    });
    wfoSelect = $("#wfo").select2({
        templateSelection: function (state) {
            return state.id;
        }
    });
    $.each(iemdata.wfos, function (idx, entry) {
        var opt = new Option("[" + entry[0] + "] " + entry[1], entry[0], false, false);
        wfoSelect.append(opt);
    });

    $(".iemdtp").datetimepicker({
        format: "L LT",
        step: 1,
        maxDate: '+1970/01/03',
        minDate: '2003/01/01',
        onClose: function (dp, $input) {
            loadData();
        }
    });
    var sts = moment().subtract(1, 'day');
    var ets = moment();
    $("#sts").val(sts.format('L LT'));
    $("#ets").val(ets.format('L LT'));
    updateRADARTimes();

    $("#load").click(function () {
        loadData();
    });
    $("#lsrshapefile").click(function () {
        window.location.href = getShapefileLink("lsr");
    });
    $("#lsrexcel").click(function () {
        window.location.href = getShapefileLink("lsr") + "&fmt=excel";
    });
    $("#warnshapefile").click(function () {
        window.location.href = getShapefileLink("watchwarn");
    });
    $("#warnexcel").click(function () {
        window.location.href = getShapefileLink("watchwarn") + "&accept=excel";
    });
    $("#sbwshapefile").click(function () {
        window.location.href = getShapefileLink("watchwarn") + "&limit1=yes";
    });
    $("#realtime").click(function () {
        realtime = this.checked;
        if (realtime) {
            loadData();
        }
    });
    olmap = new ol.Map({
        target: 'map',
        controls: ol.control.defaults.defaults().extend([new ol.control.FullScreen()]),
        view: new ol.View({
            enableRotation: false,
            center: ol.proj.transform([-94.5, 42.1], 'EPSG:4326', 'EPSG:3857'),
            zoom: 7,
            maxZoom: 16
        }),
        layers: [
            new ol.layer.Tile({
                title: 'OpenStreetMap',
                visible: true,
                type: 'base',
                source: new ol.source.OSM()
            }),
            new ol.layer.Tile({
                title: "MapTiler Toner (Black/White)",
                type: 'base',
                visible: false,
                source: new ol.source.TileJSON({
                    url: 'https://api.maptiler.com/maps/toner/tiles.json?key=d7EdAVvDI3ocoa9OUt9Z',
                    tileSize: 512,
                    crossOrigin: 'anonymous'
                })
            }),
            new ol.layer.Tile({
                title: "MapTiler Pastel",
                type: 'base',
                visible: false,
                source: new ol.source.TileJSON({
                    url: 'https://api.maptiler.com/maps/pastel/tiles.json?key=d7EdAVvDI3ocoa9OUt9Z',
                    tileSize: 512,
                    crossOrigin: 'anonymous'
                })
            }),
            n0q,
            make_iem_tms('US States', 'usstates', true, ''),
            make_iem_tms('US Counties', 'uscounties', false, ''),
            sbwLayer,
            lsrLayer
        ]
    });
    var ls = new ol.control.LayerSwitcher();
    olmap.addControl(ls);
    olmap.getInteractions().forEach(function (interaction) {
        if (interaction instanceof ol.interaction.DragPan) {
            dragPan = interaction;
        }
    });

    olmap.on('click', function (evt) {
        var feature = olmap.forEachFeatureAtPixel(evt.pixel,
            function (feature) {
                return feature;
            });
        if (feature === undefined) {
            return;
        }
        if (feature.get("phenomena") !== undefined) {
            handleSBWClick(feature);
            return;
        }
        if (feature.get('magnitude') === undefined) return;
        // evt.originalEvent.x
        var divid = revisedRandId();
        var div = document.createElement("div")
        div.innerHTML = '<div class="panel panel-primary panel-popup" id="' + divid + '">' +
            '<div class="panel-heading">' + feature.get("city") + ", " +
            feature.get("st") +
            ' &nbsp; <button type="button" class="close" ' +
            'data-target="#' + divid + '" data-dismiss="alert"> ' +
            '<span aria-hidden="true">&times;</span>' +
            '<span class="sr-only">Close</span></button></div>' +
            '<div class="panel-body">' + lsrHTML(feature) +
            '</div>' +
            '</div>';
        var coordinates = feature.getGeometry().getCoordinates();
        var marker = new ol.Overlay({
            position: coordinates,
            positioning: 'center-center',
            element: div,
            stopEvent: false,
            dragging: false
        });
        olmap.addOverlay(marker);
        div.addEventListener('mousedown', function (evt) {
            dragPan.setActive(false);
            marker.set('dragging', true);
        });
        olmap.on('pointermove', function (evt) {
            if (marker.get('dragging') === true) {
                marker.setPosition(evt.coordinate);
            }
        });
        olmap.on('pointerup', function (evt) {
            if (marker.get('dragging') === true) {
                dragPan.setActive(true);
                marker.set('dragging', false);
            }
        });
        var id = feature.getId();
        lsrtable.rows().deselect();
        lsrtable.row(
            lsrtable.rows(function (idx, data, node) {
                if (data["id"] === id) {
                    lsrtable.row(idx).select();
                    return true;
                }
                return false;
            })
        ).show().draw(false);


    });

    lsrtable = $("#lsrtable").DataTable({
        select: true,
        rowId: 'id',
        columns: [
            {
                "data": "valid",
                "visible": false
            }, {
                "className": 'details-control',
                "orderable": false,
                "data": null,
                "defaultContent": ''
            }, {
                "data": "wfo"
            }, {
                "data": "valid",
                "type": "datetime",
                "orderData": [0]
            }, {
                "data": "county"
            }, {
                "data": "city"
            }, {
                "data": "st"
            }, {
                "data": "typetext"
            }, {
                "data": "magnitude"
            }
        ],
        columnDefs: [
            {
                targets: 3,
                render: function (data) {
                    return moment.utc(data).local().format('M/D LT');
                }
            }
        ]
    });
    lsrtable.on("search.dt", function () {
        lsrLayer.dispatchEvent(TABLE_FILTERED_EVENT);
    });
    // Add event listener for opening and closing details
    $('#lsrtable tbody').on('click', 'td.details-control', function () {
        var tr = $(this).closest('tr');
        var row = lsrtable.row(tr);

        if (row.child.isShown()) {
            // This row is already open - close it
            row.child.hide();
            tr.removeClass('shown');
        }
        else {
            // Open this row
            row.child(formatLSR(row.data())).show();
            tr.addClass('shown');
        }
    });
    sbwtable = $("#sbwtable").DataTable({
        columns: [
            {
                "data": "issue",
                "visible": false
            }, {
                "data": "expire",
                "visible": false
            }, {
                "data": "wfo"
            }, {
                "data": "phenomena"
            }, {
                "data": "significance"
            }, {
                "data": "eventid"
            }, {
                "data": "issue",
                "orderData": [0]
            }, {
                "data": "expire",
                "orderData": [1]
            }
        ],
        columnDefs: [
            {
                targets: 3,
                render: function (data) {
                    return data in iemdata.vtec_phenomena ? iemdata.vtec_phenomena[data] : data;
                }
            }, {
                targets: 4,
                render: function (data) {
                    return data in iemdata.vtec_significance ? iemdata.vtec_significance[data] : data;
                }
            }, {
                targets: 5,
                render: function (data, type, row, meta) {
                    if (type == 'display') {
                        return '<a href="' + row.href + '">' + row.eventid + '</a>';
                    }
                    return row.eventid;
                }
            }, {
                targets: [6, 7],
                render: function (data) {
                    return moment.utc(data).local().format('M/D LT');
                }
            }
        ]
    });
    sbwtable.on("search.dt", function () {
        sbwLayer.dispatchEvent(TABLE_FILTERED_EVENT);
    });
}

function genSettings() {
    /* Generate URL options set on this page */
    var s = "";
    s += (n0q.visibility ? "1" : "0");
    s += (lsrLayer.visibility ? "1" : "0");
    s += (sbwLayer.visibility ? "1" : "0");
    s += (realtime ? "1" : "0");
    return s;
}

function updateURL() {
    var wfos = $("#wfo").val();  // null for all or array
    var sts = moment($("#sts").val(), 'L LT').utc().format(dateFormat1);
    var ets = moment($("#ets").val(), 'L LT').utc().format(dateFormat1);
    var wstr = (wfos === null) ? "" : wfos.join(",");
    window.location.href = "#" + wstr + "/" + sts + "/" + ets + "/" + genSettings();

}
function applySettings(opts) {
    if (opts[0] == "1") { // Show RADAR
        n0q.setVisibility(true);
    }
    if (opts[1] == "1") { // Show LSRs
        lsrLayer.setVisibility(true);
    }
    if (opts[2] == "1") { // Show SBWs
        sbwLayer.setVisibility(true);
    }
    if (opts[3] == "1") { // Realtime
        realtime = true;
        $("#realtime").prop('checked', true);
    }
}
function updateRADARTimes() {
    // Figure out what our time slider should look like
    var sts = moment($("#sts").val(), 'L LT').utc();
    var ets = moment($("#ets").val(), 'L LT').utc();
    sts.subtract(sts.minute() % 5, 'minutes');
    ets.add(5 - ets.minute() % 5, 'minutes');
    var times = ets.diff(sts) / 300000;  // 5 minute bins
    nexradBaseTime = sts;
    $("#timeslider")
        .slider("option", "max", times - 1)
        .slider("value", realtime ? times - 1 : 0);
}
function loadData() {
    // Load up the data please!
    if ($(".tab .active > a").attr("href") != "#2a") {
        $("#lsrtab").click();
    }
    var wfos = $("#wfo").val();  // null for all or array
    var sts = moment($("#sts").val(), 'L LT').utc().format(dateFormat1);
    var ets = moment($("#ets").val(), 'L LT').utc().format(dateFormat1);
    updateRADARTimes();

    var opts = {
        sts: sts,
        ets: ets,
        wfos: (wfos === null) ? "" : wfos.join(",")
    }
    lsrLayer.getSource().clear(true);
    sbwLayer.getSource().clear(true);

    $.ajax({
        data: opts,
        method: "GET",
        url: "/geojson/lsr.php",
        dataType: 'json',
        success: function (data) {
            if (data.features.length == 3000) {
                alert("App limit of 3,000 LSRs reached.");
            }
            lsrLayer.getSource().addFeatures(
                (new ol.format.GeoJSON({ featureProjection: 'EPSG:3857' })
                ).readFeatures(data)
            );
        }
    });
    $.ajax({
        data: opts,
        method: "GET",
        url: "/geojson/sbw.php",
        dataType: 'json',
        success: function (data) {
            sbwLayer.getSource().addFeatures(
                (new ol.format.GeoJSON({ featureProjection: 'EPSG:3857' })
                ).readFeatures(data)
            );
        }
    });
    updateURL();
}

function getShapefileLink(base) {
    var uri = "/cgi-bin/request/gis/" + base + ".py?";
    var wfos = $("#wfo").val();
    if (wfos) {
        for (var i = 0; i < wfos.length; i++) {
            uri += "&wfo[]=" + wfos[i];
        }
    }
    var sts = moment($("#sts").val(), 'L LT');
    var ets = moment($("#ets").val(), 'L LT');
    uri += "&year1=" + sts.utc().format('Y');
    uri += "&month1=" + sts.utc().format('M');
    uri += "&day1=" + sts.utc().format('D');
    uri += "&hour1=" + sts.utc().format('H');
    uri += "&minute1=" + sts.utc().format('m');
    uri += "&year2=" + ets.utc().format('Y');
    uri += "&month2=" + ets.utc().format('M');
    uri += "&day2=" + ets.utc().format('D');
    uri += "&hour2=" + ets.utc().format('H');
    uri += "&minute2=" + ets.utc().format('m');
    return uri;
}
