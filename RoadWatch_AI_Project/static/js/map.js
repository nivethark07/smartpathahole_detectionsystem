document.addEventListener('DOMContentLoaded', () => {
  const el = document.getElementById('damage-map');
  if (!el) return;
  if (typeof L === 'undefined') { document.getElementById('map-fallback').hidden = false; return; }
  const points = window.ROADWATCH_POINTS || [];
  const map = L.map('damage-map', {scrollWheelZoom: false}).setView([13.0827, 80.2707], 11);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19, attribution: '&copy; OpenStreetMap contributors'}).addTo(map);
  const colors = {High:'#f04444', Medium:'#e9a23b', Low:'#22a06b'};
  const bounds = [];
  points.forEach(p => {
    if (typeof p.lat !== 'number' || typeof p.lon !== 'number') return;
    const marker = L.circleMarker([p.lat, p.lon], {radius: 9, color: colors[p.severity] || '#6a7bff', fillColor: colors[p.severity] || '#6a7bff', fillOpacity: .9, weight: 2}).addTo(map);
    marker.bindPopup(`<strong>${escapeHtml(p.title)}</strong><br>${escapeHtml(p.damage_type)} · ${escapeHtml(p.severity)}<br>Status: ${escapeHtml(p.status)}<br><a href="/reports/${p.id}">View report →</a>`);
    bounds.push([p.lat, p.lon]);
  });
  if (bounds.length > 1) map.fitBounds(bounds, {padding:[30,30], maxZoom: 14});
  else if (bounds.length === 1) map.setView(bounds[0], 14);
});
function escapeHtml(s) { return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
