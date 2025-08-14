// Disable WebSocket connections to prevent HTTPS/WSS errors
(function() {
  const originalWebSocket = window.WebSocket;
  window.WebSocket = function(url, protocols) {
    // Return a mock WebSocket that doesn't actually connect
    return {
      readyState: 3, // CLOSED
      close: function() {},
      addEventListener: function() {},
      removeEventListener: function() {},
      send: function() {},
      onopen: null,
      onclose: null,
      onerror: null,
      onmessage: null
    };
  };
})();