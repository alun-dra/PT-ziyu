var SANTIAGO_LAT = -33.4489;
var SANTIAGO_LNG = -70.6693;
var DEFAULT_ZOOM = 12;

function initRequestMap(latFieldId, lngFieldId) {
    var mapEl = document.getElementById('request-map');
    if (!mapEl) return;

    var latField = document.getElementById(latFieldId);
    var lngField = document.getElementById(lngFieldId);
    if (!latField || !lngField) return;

    var addressField = document.getElementById('id_address');

    var initialLat = parseFloat(latField.value) || SANTIAGO_LAT;
    var initialLng = parseFloat(lngField.value) || SANTIAGO_LNG;
    var hasInitialCoords = latField.value && lngField.value;

    var map = L.map('request-map').setView([initialLat, initialLng], hasInitialCoords ? 15 : DEFAULT_ZOOM);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 19,
    }).addTo(map);

    var marker = null;

    if (hasInitialCoords) {
        marker = L.marker([initialLat, initialLng]).addTo(map);
    }

    map.on('click', function (e) {
        var lat = e.latlng.lat.toFixed(7);
        var lng = e.latlng.lng.toFixed(7);

        latField.value = lat;
        lngField.value = lng;

        if (marker) {
            marker.setLatLng(e.latlng);
        } else {
            marker = L.marker(e.latlng).addTo(map);
        }

        if (addressField) {
            reverseGeocode(e.latlng.lat, e.latlng.lng, addressField);
        }
    });

    setTimeout(function () {
        map.invalidateSize();
    }, 200);
}

function reverseGeocode(lat, lng, addressField) {
    var url = 'https://nominatim.openstreetmap.org/reverse?format=json&lat=' +
        lat + '&lon=' + lng + '&zoom=18&addressdetails=1&accept-language=es';

    addressField.classList.add('form-input--loading');

    fetch(url, {
        headers: { 'User-Agent': 'ZiyuJardineria/1.0' }
    })
    .then(function (response) {
        return response.json();
    })
    .then(function (data) {
        if (data && data.display_name) {
            addressField.value = data.display_name;
            addressField.classList.remove('form-input--loading');
            addressField.classList.add('form-input--updated');
            setTimeout(function () {
                addressField.classList.remove('form-input--updated');
            }, 1500);
        }
    })
    .catch(function () {
        addressField.classList.remove('form-input--loading');
    });
}

function initDashboardMap(visits) {
    var mapEl = document.getElementById('dashboard-map');
    if (!mapEl) return;

    var map = L.map('dashboard-map').setView([SANTIAGO_LAT, SANTIAGO_LNG], DEFAULT_ZOOM);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 19,
    }).addTo(map);

    if (!visits || visits.length === 0) {
        return;
    }

    var bounds = [];

    var statusColors = {
        'Pendiente': '#f59e0b',
        'Asignada': '#3b82f6',
        'Confirmada': '#10b981',
        'Cancelada': '#ef4444',
    };

    visits.forEach(function (v) {
        var lat = parseFloat(v.lat);
        var lng = parseFloat(v.lng);

        if (isNaN(lat) || isNaN(lng)) return;

        var color = statusColors[v.status] || '#6c757d';

        var icon = L.divIcon({
            className: 'custom-marker',
            html: '<div style="background-color:' + color + ';width:14px;height:14px;border-radius:50%;border:2px solid white;box-shadow:0 2px 4px rgba(0,0,0,0.3);"></div>',
            iconSize: [14, 14],
            iconAnchor: [7, 7],
        });

        var popupContent =
            '<div style="font-family:Inter,sans-serif;font-size:13px;line-height:1.5;">' +
            '<strong>' + escapeHtml(v.client) + '</strong><br>' +
            '<span style="color:#6c757d;">' + escapeHtml(v.address) + '</span><br>' +
            '<span>' + escapeHtml(v.service) + '</span><br>' +
            '<span style="font-weight:600;">' + escapeHtml(v.status) + '</span> &middot; ' + escapeHtml(v.date) +
            '</div>';

        L.marker([lat, lng], { icon: icon })
            .bindPopup(popupContent)
            .addTo(map);

        bounds.push([lat, lng]);
    });

    if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [30, 30] });
    }

    setTimeout(function () {
        map.invalidateSize();
    }, 200);
}

function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
