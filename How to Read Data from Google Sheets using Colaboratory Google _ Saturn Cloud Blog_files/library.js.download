function trackEvent(name, sendTo, showChat, intercomName){
  // event is the javascript event object, not the event we are tracking.
  // This is the latest and greatest tracking. All
  // new things should use this
  if (!name){
    throw new Error("name is required" + obj);
  }

  if (!intercomName){
    intercomName = name;
  }
  var currentUrl = window.location.protocol + "//" + window.location.host + window.location.pathname
  console.log('sending event to intercom ' + intercomName)
  Intercom("trackEvent", intercomName, {
    'current_url': currentUrl,
    'branch': window.branch,
    "staff": window.staff,
    "hugoEnvironment": window.hugoEnvironment,
  })
  var googleParams = {}
  googleParams["branch"] = window.branch
  googleParams["staff"] = window.staff
  googleParams["hugoEnvironmnet"] = window.hugoEnvironment
  if (sendTo) {
    googleParams["send_to"] = sendTo
  }
  console.log('sending event to GA ' + name + googleParams)
  gtag('event', name, googleParams)
  if (showChat) {
    Intercom('show')
  }
}

function getParameterByName(name, url = window.location.href) {
  name = name.replace(/[\[\]]/g, '\\$&');
  var regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)'),
      results = regex.exec(url);
  if (!results) return null;
  if (!results[2]) return '';
  return decodeURIComponent(results[2].replace(/\+/g, ' '));
}

function setCookie(cookieName, cookieValue, expirationDays, path = '/') {
    const date = new Date();
    date.setTime(date.getTime() + (expirationDays * 24 * 60 * 60 * 1000));
    const expires = "expires=" + date.toUTCString();
    const newCookie = cookieName + "=" + cookieValue + "; " + expires + "; path=" + path;

    // Get existing cookies
    const existingCookies = document.cookie;

    // Check if the cookie already exists
    if (existingCookies.includes(cookieName + "=")) {
        // Split existing cookies into an array
        const cookiesArray = existingCookies.split('; ');

        // Update the value of the existing cookie
        const updatedCookies = cookiesArray.map(cookie => {
            if (cookie.startsWith(cookieName + "=")) {
                return newCookie;
            }
            return cookie;
        });

        // Join the updated cookies back into a string
        document.cookie = updatedCookies.join('; ');
    } else {
        // If the cookie doesn't exist, simply append the new cookie
        document.cookie = newCookie;
    }
}


function getCookie(cookieName) {
    const name = cookieName + "=";
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookieArray = decodedCookie.split(';');
    for (let i = 0; i < cookieArray.length; i++) {
        let cookie = cookieArray[i];
        while (cookie.charAt(0) === ' ') {
            cookie = cookie.substring(1);
        }
        if (cookie.indexOf(name) === 0) {
            return cookie.substring(name.length, cookie.length);
        }
    }
    return "";
}
