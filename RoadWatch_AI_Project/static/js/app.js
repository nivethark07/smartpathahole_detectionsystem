document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('image');
  if (fileInput) fileInput.addEventListener('change', () => {
    const file = fileInput.files && fileInput.files[0];
    const label = document.getElementById('file-name');
    const wrap = document.getElementById('image-preview-wrap');
    const preview = document.getElementById('image-preview');
    if (!file) return;
    label.textContent = file.name;
    if (file.type.startsWith('image/')) {
      preview.src = URL.createObjectURL(file); wrap.hidden = false;
    }
  });
  const gpsButton = document.getElementById('gps-button');
  if (gpsButton) gpsButton.addEventListener('click', () => {
    if (!navigator.geolocation) { alert('GPS is not supported by this browser. Enter coordinates manually.'); return; }
    gpsButton.textContent = 'Getting location…'; gpsButton.disabled = true;
    navigator.geolocation.getCurrentPosition(pos => {
      document.getElementById('latitude').value = pos.coords.latitude.toFixed(6);
      document.getElementById('longitude').value = pos.coords.longitude.toFixed(6);
      gpsButton.textContent = '✓ Location captured'; gpsButton.disabled = false;
    }, err => { alert('Could not get location. Allow location permission or enter coordinates manually.'); gpsButton.textContent = '⌖ Use my current location'; gpsButton.disabled = false; }, {enableHighAccuracy: true, timeout: 10000});
  });
});
