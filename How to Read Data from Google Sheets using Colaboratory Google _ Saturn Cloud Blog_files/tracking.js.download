
window.callbacks = [];
window.loopThroughCallbacks = function(){
  for (let i = 0; i < window.callbacks.length; i++) {
    console.log('CALLBACK', window.callbacks[i]);
    callback = window.callbacks[i][0];
    callback = window.callbacks[i][0];
    args = window.callbacks[i].slice(1);
    callback(...args);
  }
  window.callbacks = null;
}
window.addCallback = function(arguments) {
  if (window.callbacks === null){
    callback = arguments[0];
    callback(...arguments.slice(1));
  } else {
    window.callbacks.push(arguments);
  }
}
function setupGclid(){
  var gclid = getParameterByName('gclid');
  if (!gclid){
    return;
  }
  Intercom('update', {'gclid': gclid});
}
window.addCallback([setupGclid]);

function trackGoogleAds(){
  var campaignid = getParameterByName('campaignid');
  if (!campaignid){
    return;
  }
  Intercom('update', {'campaignid': campaignid});
  var eventName = "campaign_" + campaignid
  trackEvent(eventName);
}
window.addCallback([trackGoogleAds]);

(function(){
  var delay = 250;
  var current = null;
  var now = new Date().getTime() / 1000;
  var maxDelay = 3000;
  loop = function(){
    var newTime = new Date().getTime() / 1000;
    if (Intercom && Intercom.booted){
      window.loopThroughCallbacks();
      clearInterval(intervalId);
    } else if ((newTime - now) > maxDelay){
      window.loopThroughCallbacks();
      clearInterval(intervalId);
    }
  }
  var intervalId = setInterval(loop, 1000)
})();


$(document).ready(function(){
  document.querySelectorAll('.gtag_track').forEach((node)=>{
    if (node.href.includes("#request-a-demo") || node.href.includes("#contact-for-enterprise")){
      node.href = "/request-a-demo/#request-a-demo"
      node.addEventListener('click', (e) => {
        trackEvent("request_a_demo", null, false)
      });
    }
  });
})
