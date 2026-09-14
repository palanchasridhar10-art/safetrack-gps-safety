/**
 * Wraps the browser Geolocation API. Location is only ever requested in
 * direct response to a user action (button press) — never automatically or
 * silently on page load.
 */
function getCurrentPosition(options = {}) {
  return new Promise((resolve, reject) => {
    if (!("geolocation" in navigator)) {
      reject(new Error("Geolocation is not supported by this browser."));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        resolve({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        });
      },
      (err) => {
        if (err.code === err.PERMISSION_DENIED) {
          reject(new Error("Location access is disabled. Please enable location permission in your browser."));
        } else if (err.code === err.POSITION_UNAVAILABLE) {
          reject(new Error("Unable to obtain your current location. Please move to an area with better GPS/network availability."));
        } else if (err.code === err.TIMEOUT) {
          reject(new Error("Getting your location timed out. Please try again."));
        } else {
          reject(new Error("Could not get your location."));
        }
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0, ...options }
    );
  });
}

/** Returns a watch id; caller is responsible for clearing it via stopWatching(). */
function watchPosition(onUpdate, onError) {
  if (!("geolocation" in navigator)) {
    onError(new Error("Geolocation is not supported by this browser."));
    return null;
  }
  return navigator.geolocation.watchPosition(
    (pos) =>
      onUpdate({
        latitude: pos.coords.latitude,
        longitude: pos.coords.longitude,
        accuracy: pos.coords.accuracy,
      }),
    (err) => onError(err),
    { enableHighAccuracy: true, maximumAge: 0, timeout: 20000 }
  );
}

function stopWatching(watchId) {
  if (watchId !== null && watchId !== undefined) {
    navigator.geolocation.clearWatch(watchId);
  }
}
