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
    icon: '/favicon.png',
    badge: '/favicon-32x32.png',
    vibrate: [200, 100, 200],
    data: payload.data,
    actions: [
      {
        action: 'open',
        title: 'View Details'
      }
    ]
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  // Open the app
  event.waitUntil(
    clients.openWindow('/')
  );
});
