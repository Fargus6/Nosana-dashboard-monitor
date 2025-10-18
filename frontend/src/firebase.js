import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

const firebaseConfig = {
  apiKey: "AIzaSyDES6FP7Qe-Q26VthN5O_QKtiLhMfaDJQ0",
  projectId: "nosana-node-monitor",
  messagingSenderId: "586986709205",
  appId: "1:586986709205:web:9854b5a70a8f0892ecc11d"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Cloud Messaging
let messaging = null;
try {
  if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
    messaging = getMessaging(app);
  }
} catch (error) {
  console.error('Firebase messaging error:', error);
}

export { messaging, getToken, onMessage };

// VAPID key for web push
export const VAPID_KEY = "BD_zwmZzjsMELTILg1zpw6tI_2S2fk7qrrq4PzbYUzj8X4dRAzAUiobOAUqNyJohLebqaCF--ZeE6g38LZ8GXFs";
