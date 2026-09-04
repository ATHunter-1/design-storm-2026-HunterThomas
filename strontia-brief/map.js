/* Interactive locator map for the Strontia Springs brief.
 *
 * Loads the committed GeoJSON directly, so basins/*.json and places.json stay the
 * single source of truth. That needs the page served over http, not opened as a
 * file:// URL, because browsers block fetch() on local files:
 *
 *     python3 eddd/data/serve.py
 *     http://localhost:8765/design-storm-strontia-springs-brief
 */
(function () {
  "use strict";

  var DATA = "strontia-brief/";
  var BASINS = {
    southPlatte: "basins/south-platte-above-strontia-06707525.json",
    trumbull: "basins/south-platte-above-trumbull-06701900.json",
    blue: "basins/blue-river-below-dillon-09050700.json",
    fraser: "basins/fraser-below-moffat-09023562.json",
    williamsFork: "basins/williams-fork-parshall-09037500.json",
    rivers: "basins/mainstem-flowlines-06707525.json",
    downstream: "basins/downstream-mainstem-06707525.json",
    conduits: "basins/conduits-osm.json"
  };

  var SILT = "#A8621B";
  var TEAL = "#068C7D";
  var INK = "#2B3634";

  var container = document.getElementById("locator-map");
  if (!container || typeof L === "undefined") return;

  function json(path) {
    return fetch(DATA + path).then(function (r) {
      if (!r.ok) throw new Error(path + " -> " + r.status);
      return r.json();
    });
  }

  /* GeoJSON is [lon, lat]; Leaflet wants [lat, lon]. */
  function toLatLngs(coords) {
    return coords.map(function (c) { return [c[1], c[0]]; });
  }

  function ringOf(featureCollection) {
    var g = featureCollection.features[0].geometry;
    return g.type === "Polygon" ? g.coordinates[0] : g.coordinates[0][0];
  }

  /* The east-facing half of a west-slope basin ring is the Continental Divide:
     the line where water stops draining to the Colorado and starts draining east. */
  function easternArc(coords) {
    var north = 0, south = 0, i;
    for (i = 1; i < coords.length; i++) {
      if (coords[i][1] > coords[north][1]) north = i;
      if (coords[i][1] < coords[south][1]) south = i;
    }
    var forward = north <= south
      ? coords.slice(north, south + 1)
      : coords.slice(north).concat(coords.slice(0, south + 1));
    var backward = (south <= north
      ? coords.slice(south, north + 1)
      : coords.slice(south).concat(coords.slice(0, north + 1))).slice().reverse();
    var meanLon = function (arc) {
      return arc.reduce(function (sum, c) { return sum + c[0]; }, 0) / arc.length;
    };
    return meanLon(forward) > meanLon(backward) ? forward : backward;
  }

  var map = L.map(container, {
    scrollWheelZoom: false,
    zoomControl: true,
    attributionControl: true
  });

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 17,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);

  /* Handy when checking the view from the console or a test harness. */
  window.__strontiaMap = map;

  /* A document that scrolls past a map should not have the map eat the scroll. */
  map.on("click", function () { map.scrollWheelZoom.enable(); });
  map.on("mouseout", function () { map.scrollWheelZoom.disable(); });

  function marker(entry, options) {
    return L.circleMarker([entry.lat, entry.lon], {
      radius: options.radius || 6,
      color: "#fff",
      weight: 2,
      fillColor: options.color,
      fillOpacity: 1
    }).bindPopup(
      '<strong>' + options.title + '</strong>' + (options.note ? '<br>' + options.note : '')
    ).bindTooltip(options.title, { direction: "top", offset: [0, -6] });
  }

  Promise.all([
    json("places.json"),
    json(BASINS.southPlatte),
    json(BASINS.trumbull),
    json(BASINS.blue),
    json(BASINS.fraser),
    json(BASINS.williamsFork),
    json(BASINS.rivers),
    json(BASINS.downstream),
    json(BASINS.conduits)
  ]).then(function (results) {
    var places = results[0];
    var southPlatte = ringOf(results[1]);
    var trumbull = ringOf(results[2]);
    var blue = ringOf(results[3]);
    var fraser = ringOf(results[4]);
    var williamsFork = ringOf(results[5]);
    var rivers = results[6].features.map(function (f) { return f.geometry.coordinates; });
    var downstream = results[7].features.map(function (f) { return f.geometry.coordinates; });
    var conduits = results[8].features;

    var gages = places.gages;
    var reservoirs = places.reservoirs;

    L.polygon(toLatLngs(southPlatte), {
      color: SILT, weight: 3, fillColor: SILT, fillOpacity: 0.28
    }).bindTooltip("Drains to the gage &middot; 2,584 sq mi").addTo(map);

    L.polygon(toLatLngs(trumbull), {
      color: "#3A4542", weight: 2.5, dashArray: "6 5", fill: false, opacity: 0.9
    }).bindTooltip("Measured by the flow gage &middot; 2,028 sq mi").addTo(map);

    [[blue, "Blue River above Dillon &middot; 320 sq mi"],
     [fraser, "Fraser below the Moffat Tunnel &middot; 31 sq mi"],
     [williamsFork, "Williams Fork &middot; 184 sq mi"]].forEach(function (pair) {
      L.polygon(toLatLngs(pair[0]), {
        color: TEAL, weight: 3, fillColor: TEAL, fillOpacity: 0.3
      }).bindTooltip(pair[1] + " &middot; west of the divide").addTo(map);
    });

    rivers.forEach(function (line) {
      L.polyline(toLatLngs(line), { color: "#0B5FA5", weight: 2, opacity: 0.9 }).addTo(map);
    });

    /* The tiles invert in dark mode but these vectors do not, so the divide gets a
       white casing under a dark core. That pairing stays legible on either ground. */
    [williamsFork, fraser, blue].forEach(function (basin) {
      var arc = toLatLngs(easternArc(basin));
      L.polyline(arc, { color: "#FFFFFF", weight: 7, opacity: 0.75 }).addTo(map);
      L.polyline(arc, {
        color: INK, weight: 3.5, opacity: 0.95, dashArray: "10 7"
      }).bindTooltip("Continental Divide").addTo(map);
    });

    L.polyline([
      [reservoirs.dillon.lat, reservoirs.dillon.lon],
      [gages.north_fork_at_grant.lat, gages.north_fork_at_grant.lon]
    ], { color: "#B0197A", weight: 4, dashArray: "9 6", opacity: 0.95 })
      .bindTooltip("Roberts Tunnel &middot; 23 miles under the divide")
      .addTo(map);

    marker(gages.turbidity, {
      color: SILT, radius: 9, title: "Strontia Springs gage 06707525",
      note: "The sensor this brief is about. Sits just above Strontia Springs Reservoir, through which Denver Water says 80% of its supply passes."
    }).addTo(map).openPopup();

    marker(gages.flow, {
      color: "#7A8783", title: "Flow gage 06701900, Trumbull",
      note: "Measures 2,028 of the 2,584 sq mi reaching Strontia Springs. Registered nothing during the storm."
    }).addTo(map);

    marker(places.places.denver, {
      color: INK, radius: 8, title: "Denver",
      note: "24 miles (38 km) north-east of the gage."
    }).addTo(map);

    marker(reservoirs.dillon, {
      color: TEAL, title: "Dillon Reservoir",
      note: "West of the divide, on the Blue River. The Roberts Tunnel starts here."
    }).addTo(map);

    marker(gages.north_fork_at_grant, {
      color: TEAL, title: "Grant &middot; east portal",
      note: "Blue River water surfaces here after 23 miles underground, then travels the rest of the way as an ordinary river."
    }).addTo(map);

    marker(gages.north_fork_confluence, {
      color: "#7A8783", radius: 5, title: "Confluence at South Platte",
      note: "The North Fork joins the mainstem 2.3 km above the gage, which is why the gage reads the combined inflow."
    }).addTo(map);

    [[reservoirs.cheesman, "Cheesman Reservoir"],
     [reservoirs.eleven_mile, "Eleven Mile Canyon Reservoir"],
     [reservoirs.antero, "Antero Reservoir"]].forEach(function (pair) {
      marker(pair[0], {
        color: SILT, radius: 5, title: pair[1], note: "Upper South Platte storage, east of the divide."
      }).addTo(map);
    });

    /* --- What happens to the water after the gage --- */

    var SUPPLY = "#B0197A";
    var facilities = places.facilities;
    var dam = [facilities.strontia_springs_dam.lat, facilities.strontia_springs_dam.lon];

    /* The river below the gage, real channel geometry, split at the dam itself.
       NLDI returns these segments already ordered downstream and joined end to end,
       so they flatten into one path and the split is a single index, not a
       per-segment guess. Above the dam is the water heading into the reservoir;
       below it the river carries on north and is no longer the drinking supply. */
    var channel = [];
    downstream.forEach(function (line) {
      toLatLngs(line).forEach(function (point) {
        var last = channel[channel.length - 1];
        if (!last || last[0] !== point[0] || last[1] !== point[1]) channel.push(point);
      });
    });

    var damIndex = 0;
    var closest = Infinity;
    channel.forEach(function (point, i) {
      var d = Math.pow(point[0] - dam[0], 2) + Math.pow(point[1] - dam[1], 2);
      if (d < closest) { closest = d; damIndex = i; }
    });

    L.polyline(channel.slice(0, damIndex + 1), {
      color: SUPPLY, weight: 4, opacity: 0.95
    }).bindTooltip("The measured water, flowing into Strontia Springs Reservoir").addTo(map);

    L.polyline(channel.slice(damIndex), {
      color: "#0B5FA5", weight: 2, opacity: 0.55, dashArray: "4 5"
    }).bindTooltip("River below the dam &middot; carries on north, not the drinking supply").addTo(map);

    /* Two intakes, not one. Denver Water's 2015 Source Water Protection Plan:
       "an intake at Strontia Springs Reservoir and one just downstream in Waterton
       Canyon". Foothills is fed from the reservoir; Marston is fed from the Marston
       Diversion Dam 2.6 mi below it, which sits 24 m from the head of Conduit 20.
       That is why the IWRP pairs Conduit 20 with the Platte Canyon Intake Dam rather
       than with Strontia: they are the same structure under a different name. */
    conduits.forEach(function (feature) {
      var name = feature.properties.name;
      var isConduit20 = /^Conduit 20$/i.test(name);
      var isAurora = /Aurora/i.test(name);
      if (!isConduit20 && !isAurora) return;
      L.polyline(toLatLngs(feature.geometry.coordinates), {
        color: isConduit20 ? SUPPLY : "#6B7A76",
        weight: isConduit20 ? 4 : 3,
        opacity: isConduit20 ? 0.95 : 0.8,
        dashArray: isConduit20 ? null : "3 6"
      }).bindTooltip(isConduit20
        ? "Conduit 20 &middot; the measured water on its way to Marston &middot; mapped route"
        : name + " &middot; Aurora Water, which has its own intake at the dam"
      ).addTo(map);
    });

    /* Reservoir to Foothills via Conduit 26. Drawn from the state register's intake
       coordinate rather than the dam. Still a straight line: Conduit 26 is not mapped
       in OSM and no public route geometry exists. But Denver Water's audited accounts
       put it at 3.7-3.8 miles, and the intake sits 3.53 miles from the nearest plant
       boundary, so a near-straight alignment is what the numbers imply. */
    var c26 = facilities.conduit_26_intake;
    L.polyline([[c26.lat, c26.lon], [facilities.foothills_plant.lat, facilities.foothills_plant.lon]], {
      color: SUPPLY, weight: 3.5, dashArray: "2 7", opacity: 0.9, lineCap: "round"
    }).bindTooltip("Conduit 26 to Foothills &middot; 3.7 miles, 750 MGD &middot; alignment schematic").addTo(map);

    marker(c26, {
      color: SUPPLY, radius: 6, title: "Conduit 26 intake",
      note: "Colorado's structure register calls this asset DENVER FOOTHILLS PL 26 and lists STRONTIA SPRINGS DENVER INTAKE among its aliases. 120-inch steel pipe, 3.7 miles, 750 million gallons a day, in service since 1983."
    }).addTo(map);

    marker(facilities.marston_diversion_dam, {
      color: SUPPLY, radius: 7, title: "Marston Diversion Dam",
      note: "The second intake, 2.6 miles below Strontia Springs Dam. Water released from the reservoir is re-diverted here into Conduit 20 and carried to Marston. Denver Water also calls this the Platte Canyon Diversion Dam and the Platte Canyon Intake Dam."
    }).addTo(map);

    marker(reservoirs.chatfield, {
      color: "#7A8783", radius: 5, title: "Chatfield Reservoir",
      note: "Army Corps flood control, downstream of Waterton Canyon. <em>Not</em> on the drinking water path: Denver Water uses storage here to capture bypass flows released from Strontia Springs."
    }).addTo(map);

    marker(reservoirs.williams_fork_reservoir, {
      color: TEAL, radius: 5, title: "Williams Fork Reservoir", note: "West of the divide."
    }).addTo(map);

    marker(gages.fraser_below_moffat, {
      color: TEAL, radius: 5, title: "Fraser gage, below the Moffat Tunnel", note: "West of the divide."
    }).addTo(map);

    /* extend() takes one point at a time, so collect every corner first. */
    var extent = toLatLngs(southPlatte)
      .concat(toLatLngs(blue), toLatLngs(fraser), toLatLngs(williamsFork))
      .concat([[places.places.denver.lat, places.places.denver.lon]]);
    map.fitBounds(L.latLngBounds(extent), { padding: [26, 26] });
  }).catch(function (err) {
    container.innerHTML =
      '<p style="padding:20px;margin:0">Map data did not load: ' + err.message +
      '. This page needs to be served over http, not opened as a file. Run ' +
      '<code>python3 eddd/data/serve.py</code> and open ' +
      '<code>http://localhost:8765/design-storm-strontia-springs-brief</code>.</p>';
  });
})();
