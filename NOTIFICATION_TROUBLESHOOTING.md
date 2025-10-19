# 📱 Mobile Notification Troubleshooting Guide

## Current Issue
Push notifications are not appearing on mobile phone.

## Diagnostic Results
✅ Firebase configured correctly (backend & frontend)
✅ Service worker registered and working
✅ Notification code properly implemented
❌ **No device tokens registered in database**

## Root Cause
The notifications aren't working because no device token has been registered yet. This means either:
1. You haven't enabled notifications in the app yet, OR
2. The notification permission was denied, OR
3. The browser/device doesn't support notifications

## Step-by-Step Fix

### 1️⃣ **Check Your Setup**

**Requirements:**
- ✅ Must use **Chrome** on Android or **Safari** on iOS
- ✅ Must access app via **HTTPS** (https://nosanamonitor.preview.emergentagent.com)
- ✅ Device must support service workers and notifications
- ✅ Must be **logged in** to the app

### 2️⃣ **Enable Notifications (Critical Step)**

1. **Login to your account**
   - Go to: https://nosanamonitor.preview.emergentagent.com
   - Login with your credentials

2. **Open Settings**
   - Look for the **gear icon (⚙️)** in the top header
   - Click on it to open the Settings modal

3. **Enable Push Notifications**
   - Click the **"Enable Notifications"** button
   - Browser will show a permission dialog
   - Click **"Allow"** or **"Yes"**

4. **Verify Success**
   - You should see: ✅ "Push notifications enabled!"
   - Click **"Send Test Notification"** button
   - You should receive a test notification immediately

### 3️⃣ **Configure Notification Preferences**

After enabling, set your preferences:
- ✅ Node comes online
- ✅ Node goes offline
- ✅ Job started on node
- ✅ Job completed on node
- ✅ Sound enabled
- ✅ Vibration enabled

Click **"Save Preferences"**

### 4️⃣ **Test Notifications**

**Option A: Use Test Button**
1. In Settings modal, click **"Send Test Notification"**
2. Should receive notification immediately

**Option B: Trigger Real Event**
1. Wait for a node status change (online/offline)
2. Wait for a job to start/complete
3. Notification should appear automatically

## 🔍 Debugging on Mobile

### Check Browser Console

1. **Open DevTools on Mobile:**
   - **Chrome Android**: Menu → More Tools → Developer Tools
   - **Safari iOS**: Settings → Safari → Advanced → Web Inspector

2. **Look for these messages in Console:**
   ```
   ✅ "Notification permission granted"
   ✅ "Service Worker registered"
   ✅ "FCM Token obtained: ..."
   ✅ "Registering token with backend..."
   ✅ "Push notifications enabled!"
   ```

3. **Check for errors:**
   ```
   ❌ "Notifications not supported in this browser"
   ❌ "Notification permission denied"
   ❌ "Failed to obtain FCM token"
   ❌ "Service Workers not supported"
   ```

### Check Service Worker Status

1. **Chrome Android:**
   - DevTools → Application tab → Service Workers
   - Should see: `firebase-messaging-sw.js` (status: activated)

2. **Safari iOS:**
   - Web Inspector → Sources → Service Workers
   - Should see service worker registered

### Check Notification Permission

1. **Chrome:**
   - Click padlock icon in address bar
   - Check "Notifications" permission
   - Should be "Allowed"

2. **Safari:**
   - Settings → Safari → Notifications
   - Find your app domain
   - Should be "Allow"

## Common Issues & Solutions

### ❌ Issue 1: "Notifications not supported in this browser"
**Solution:**
- Use Chrome on Android (v63+)
- Use Safari on iOS (v16.4+)
- Update your browser to latest version
- Ensure you're on HTTPS, not HTTP

### ❌ Issue 2: "Notification permission denied"
**Solution:**
- Go to browser settings
- Find site permissions for alert-hub-11.preview.emergentagent.com
- Change notification permission to "Allow"
- Refresh the page and try again

### ❌ Issue 3: "Failed to obtain FCM token"
**Solution:**
- Clear browser cache and data
- Unregister old service workers (DevTools → Application → Service Workers → Unregister)
- Refresh page
- Try enabling notifications again

### ❌ Issue 4: Notifications enabled but not receiving any
**Solution:**
1. Check if device token is registered:
   - Backend logs should show: "Device token registered"
   - Or contact support to check database

2. Check notification preferences:
   - Open Settings modal
   - Verify at least one notification type is enabled
   - Save preferences

3. Test with "Send Test Notification" button

4. Check phone notification settings:
   - Ensure phone is not in "Do Not Disturb" mode
   - Check notification volume/vibration is on
   - Check battery saver isn't blocking notifications

### ❌ Issue 5: Service worker not registering
**Solution:**
```javascript
// Check service worker in DevTools console:
navigator.serviceWorker.getRegistrations().then(regs => {
  console.log('Registered service workers:', regs);
  regs.forEach(reg => console.log('SW:', reg.active?.scriptURL));
});

// Check Firebase messaging:
console.log('Messaging supported:', 'serviceWorker' in navigator);
console.log('Notification permission:', Notification.permission);
```

## 📊 Verification Checklist

Before reporting issue, verify:

- [ ] Logged into the app
- [ ] Accessed via HTTPS URL
- [ ] Using Chrome (Android) or Safari (iOS)
- [ ] Browser notifications enabled in phone settings
- [ ] Clicked "Enable Notifications" in Settings modal
- [ ] Clicked "Allow" on browser permission dialog
- [ ] Saw success message: "Push notifications enabled!"
- [ ] Clicked "Send Test Notification" button
- [ ] At least one notification preference is enabled
- [ ] Phone not in Do Not Disturb mode
- [ ] Phone volume/vibration is on

## 🆘 Still Not Working?

If you've completed all steps above and notifications still don't work:

### Collect Debug Information:

1. **Browser Info:**
   ```javascript
   // Run in DevTools console:
   console.log('User Agent:', navigator.userAgent);
   console.log('Service Worker support:', 'serviceWorker' in navigator);
   console.log('Notification permission:', Notification.permission);
   console.log('Push API support:', 'PushManager' in window);
   ```

2. **Check Backend Logs:**
   ```bash
   # On server, check for notification attempts:
   tail -100 /var/log/supervisor/backend.err.log | grep -i "notif"
   ```

3. **Check Database:**
   - Verify device token is registered
   - Verify notification preferences are saved
   - Verify user ID matches

### Contact Support With:
- Device model and OS version
- Browser name and version
- Debug information from above
- Screenshots of Settings modal
- Any error messages in console

## 📱 Android-Specific Tips

1. **Chrome Notifications:**
   - Ensure Chrome has notification permission in Android Settings
   - Check: Settings → Apps → Chrome → Notifications → Allowed

2. **Battery Optimization:**
   - Disable battery optimization for Chrome
   - Settings → Battery → Battery Optimization → Chrome → Don't optimize

3. **Data Saver:**
   - Turn off Data Saver in Chrome
   - Chrome Menu → Settings → Lite mode → Off

## 🍎 iOS-Specific Tips

1. **Safari Notifications:**
   - iOS 16.4+ required for web push notifications
   - Update iOS if on older version

2. **Add to Home Screen:**
   - For best results, "Add to Home Screen" as PWA
   - Safari → Share → Add to Home Screen
   - Open from home screen icon

3. **Focus Modes:**
   - Check that Focus mode isn't blocking notifications
   - Settings → Focus → Check allowed notifications

## 🔔 Testing Notification Delivery

### Test Sequence:

1. **Enable notifications** (one-time setup)
2. **Send test notification** (should arrive immediately)
3. **Add a node** with valid Solana address
4. **Wait for status change** (or trigger manually)
5. **Check if real notification arrives**

### Expected Behavior:

- Test notification: Immediate delivery
- Status change notification: Within ~30 seconds of change
- Notification should:
  - ✅ Appear on lock screen
  - ✅ Play sound (if enabled)
  - ✅ Vibrate (if enabled)
  - ✅ Show notification badge
  - ✅ Be tappable to open app

## 📞 Quick Help Commands

Run these in your browser DevTools console for quick diagnostics:

```javascript
// Check notification permission
console.log('Permission:', Notification.permission);

// Check service workers
navigator.serviceWorker.getRegistrations().then(r => console.log('SWs:', r));

// Request notification permission
Notification.requestPermission().then(p => console.log('Permission:', p));

// Test browser notification (not Firebase)
new Notification('Test', { body: 'If you see this, browser notifications work!' });
```

## ✅ Success Indicators

You'll know notifications are working when:

1. ✅ Settings modal shows "Push notifications enabled"
2. ✅ Test notification appears on your phone
3. ✅ Backend logs show "Device token registered for user: [your-user-id]"
4. ✅ Real status change triggers notification
5. ✅ Notification appears on lock screen
6. ✅ Tapping notification opens the app

---

**Last Updated:** October 18, 2024
**App URL:** https://nosanamonitor.preview.emergentagent.com
**Support:** Check DevTools console for detailed error messages
