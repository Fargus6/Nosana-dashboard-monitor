// Firebase Cloud Messaging Service Worker
importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyDES6FP7Qe-Q26VthN5O_QKtiLhMfaDJQ0",
  projectId: "nosana-node-monitor",
  messagingSenderId: "586986709205",
  appId: "1:586986709205:web:9854b5a70a8f0892ecc11d"
});

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('Received background message:', payload);

  const notificationTitle = payload.notification?.title || 'Nosana Node Monitor';
  const notificationOptions = {
    body: payload.notification?.body || 'New notification',
    icon: '/logo192.png',
    badge: '/favicon-32x32.png',
    
    // Critical for lock screen display
    requireInteraction: false,  // Don't require user interaction to dismiss
    silent: false,  // Play sound
    
    // Wake up screen and show on lock screen
    tag: 'nosana-node-alert',  // Replace previous notifications with same tag
    renotify: true,  // Vibrate even if notification with same tag exists
    
    // Vibration pattern (vibrate-pause-vibrate)
    vibrate: [300, 100, 300, 100, 300],  // Stronger pattern
    
    // Priority and visibility
    // Note: These work on Android, iOS has different handling
    priority: 'high',
    visibility: 'public',  // Show on lock screen
    
    // Data payload
    data: {
      ...payload.data,
      url: '/',
      timestamp: Date.now()
    },
    
    // Action buttons
    actions: [
      {
        action: 'open',
        title: 'Open App',
        icon: '/favicon-32x32.png'
      },
      {
        action: 'close',
        title: 'Dismiss'
      }
    ],
    
    // Image for rich notification (optional)
    image: payload.notification?.image || null
  };

  return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event.action);
  event.notification.close();
  
  // Handle different actions
  if (event.action === 'close') {
    // Just close the notification
    return;
  }
  
  // For 'open' action or clicking the notification body
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if app is already open
        for (let client of clientList) {
          if (client.url.includes(self.registration.scope) && 'focus' in client) {
            return client.focus();
          }
        }
        // If not open, open a new window
        if (clients.openWindow) {
          return clients.openWindow('/');
        }
      })
  );
});

// Handle notification close event
self.addEventListener('notificationclose', (event) => {
  console.log('Notification closed:', event.notification.tag);
});
