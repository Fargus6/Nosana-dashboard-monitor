# 🍎 iOS Push Notifications Setup Guide

## ⚠️ CRITICAL: iOS Requires PWA Installation

**On iOS (iPhone/iPad), web push notifications ONLY work when the app is installed to your home screen as a PWA (Progressive Web App).**

Regular Safari browsing **DOES NOT** support push notifications on iOS!

---

## ✅ Complete iOS Setup (5 Minutes)

### Step 1: Install App to Home Screen (Required!)

1. **Open Safari** on your iPhone
   - Go to: https://nosana-monitor.preview.emergentagent.com
   - ⚠️ Must use **Safari**, not Chrome or other browsers

2. **Tap the Share button**
   - Look for the share icon (square with arrow pointing up)
   - It's at the bottom of the screen in Safari

3. **Scroll down and tap "Add to Home Screen"**
   - You'll see the app icon and name
   - Tap "Add" in the top right

4. **App icon appears on your home screen**
   - Look for "Nosana Monitor" icon
   - Tap it to open the app

### Step 2: Login to Your Account

1. **Open the app from home screen** (not Safari!)
2. Login with your credentials
3. Make sure you're logged in successfully

### Step 3: Enable Push Notifications

1. **Tap Settings icon** (⚙️) in the app header

2. **Tap "Enable Notifications"** button

3. **iOS will ask for permission**
   - Tap "Allow"
   - ⚠️ If you tap "Don't Allow", you'll need to enable manually in Settings

4. **Success!**
   - You should see: "🎉 Push notifications enabled!"

### Step 4: Configure Preferences

1. **In the Settings modal, check:**
   - ✅ Node comes online
   - ✅ Node goes offline
   - ✅ Job started on node
   - ✅ Job completed on node
   - ✅ Sound enabled
   - ✅ Vibration enabled

2. **Tap "Save Preferences"**

### Step 5: Test It

1. **Tap "Send Test Notification"** in Settings modal

2. **Lock your iPhone**
   - Press the power button

3. **Notification should appear on lock screen!**
   - If it doesn't, continue to troubleshooting below

---

## 🔍 Troubleshooting for iOS

### Issue 1: Not seeing "Add to Home Screen" option

**Solution:**
- Make sure you're in **Safari** (not Chrome, Firefox, etc.)
- Tap the Share button (not the tab button)
- Scroll down in the share menu to find "Add to Home Screen"

### Issue 2: Notification permission not appearing

**Reasons:**
1. **Not opened from home screen icon**
   - You MUST open the app from the home screen icon, not Safari
   - Delete the app from home screen and re-add it
   - Open from the newly added icon

2. **Previously denied permission**
   - Go to: Settings → Nosana Monitor → Notifications
   - Toggle "Allow Notifications" ON
   - Return to app and try "Enable Notifications" again

3. **Focus Mode is on**
   - Disable Focus modes temporarily
   - Settings → Focus → Turn off all Focus modes

### Issue 3: Enabled but not receiving notifications

**Check these iOS settings:**

1. **App Notification Settings**
   ```
   Settings → Nosana Monitor → Notifications
   
   Should be:
   ✅ Allow Notifications: ON
   ✅ Lock Screen: ON
   ✅ Notification Center: ON
   ✅ Banners: ON
   ✅ Sounds: ON
   ✅ Badges: ON
   ```

2. **Focus Modes**
   ```
   Settings → Focus
   
   Check:
   - No Focus mode is active
   - OR Nosana Monitor is allowed in active Focus mode
   ```

3. **Screen Time**
   ```
   Settings → Screen Time → Content & Privacy
   
   Check:
   - Notifications are not restricted
   ```

4. **Do Not Disturb**
   ```
   Control Center
   
   Check:
   - Do Not Disturb is OFF
   - Focus mode is OFF
   ```

### Issue 4: Test notification not appearing

**Try this sequence:**

1. **Close the app completely**
   - Swipe up from home screen
   - Swipe up on Nosana Monitor to close

2. **Open iOS Settings → Notifications**
   - Find "Nosana Monitor"
   - Make sure it's listed (if not, app needs to be re-installed)
   - Toggle all notification options ON

3. **Reopen app from home screen**
   - Go to Settings in app
   - Try "Send Test Notification" again

4. **Lock your phone immediately after tapping**
   - Notification should appear on lock screen

### Issue 5: Service worker not registering

**Solution:**

1. **Clear Safari cache:**
   ```
   iOS Settings → Safari → Clear History and Website Data
   ```

2. **Remove app from home screen:**
   - Long press the app icon
   - Tap "Remove App" → "Delete App"

3. **Re-add to home screen:**
   - Open Safari → Go to app URL
   - Share → Add to Home Screen

4. **Try enabling notifications again**

---

## 📱 iOS Version Requirements

- **Minimum:** iOS 16.4
- **Your version:** iOS 18.7.1 ✅ (Supported!)
- **Browser:** Safari only
- **Installation:** Must be added to home screen

---

## 🔬 Advanced Debugging for iOS

### Check if app is installed as PWA:

1. **Open the app from home screen**

2. **Open Web Inspector** (if you have Mac):
   - Mac: Safari → Develop → [Your iPhone] → [Nosana Monitor]
   - Look at Console for errors

3. **Check service worker:**
   ```javascript
   // In Web Inspector Console:
   navigator.serviceWorker.getRegistrations().then(regs => {
     console.log('Service workers:', regs.length);
     regs.forEach(reg => console.log('SW:', reg.active?.scriptURL));
   });
   ```

4. **Check notification permission:**
   ```javascript
   console.log('Permission:', Notification.permission);
   console.log('In standalone:', window.navigator.standalone);
   ```

### Expected Console Output:

```javascript
✅ Permission: "granted" (or "default" if not enabled yet)
✅ In standalone: true (means opened as PWA)
✅ Service workers: 1
✅ SW: https://nosana-monitor.preview.emergentagent.com/firebase-messaging-sw.js
```

---

## ⚡ Quick Checklist

Before reporting issues, verify:

- [ ] iOS 16.4 or later (you have 18.7.1 ✅)
- [ ] Using Safari browser for installation
- [ ] App added to home screen (not just bookmarked)
- [ ] Opened app from home screen icon (not Safari)
- [ ] Logged into your account in the PWA
- [ ] Clicked "Enable Notifications" button
- [ ] Allowed permission when iOS asked
- [ ] Notifications enabled in iOS Settings → Nosana Monitor
- [ ] Lock Screen, Banners, Sounds all ON
- [ ] Not in Focus mode or Do Not Disturb
- [ ] Tested with "Send Test Notification" button
- [ ] Locked phone to check lock screen

---

## 🎯 Common Mistakes

### ❌ Wrong: Opening in Safari browser
```
Safari → Browse to URL → Try to enable notifications
Result: Won't work on iOS!
```

### ✅ Correct: Opening as installed PWA
```
Safari → Add to Home Screen → Open from home screen icon → Enable notifications
Result: Works!
```

---

## 📞 Still Not Working?

If you've completed ALL steps above and it still doesn't work:

### Collect this information:

1. **Screenshot of:**
   - Settings → Nosana Monitor → Notifications screen
   - App Settings modal with notifications section
   - Home screen showing the app icon

2. **Confirm:**
   - You added app to home screen (not just bookmark)
   - You're opening from home screen icon
   - You're logged in when enabling notifications
   - You see the "Enable Notifications" button in Settings

3. **Try these tests:**

```javascript
// Open Web Inspector and run:
console.log('iOS Version:', navigator.userAgent);
console.log('Standalone mode:', window.navigator.standalone);
console.log('Service Worker support:', 'serviceWorker' in navigator);
console.log('Notification permission:', Notification.permission);
console.log('Push support:', 'PushManager' in window);

// Should show:
// iOS Version: ...iOS 18.7.1...
// Standalone mode: true  ← MUST be true!
// Service Worker support: true
// Notification permission: "granted" (or "default")
// Push support: true
```

---

## 🆘 Last Resort: Complete Reset

If nothing works, try this complete reset:

1. **Remove app from home screen**
   - Long press → Remove App → Delete App

2. **Clear all Safari data**
   - Settings → Safari → Clear History and Website Data
   - Confirm clear

3. **Restart your iPhone**
   - Power off completely
   - Turn back on

4. **Re-install fresh:**
   - Safari → Go to app URL
   - Add to Home Screen
   - Open from home screen icon
   - Login
   - Enable notifications
   - Test

---

## ✅ Success Indicators

You'll know it's working when:

1. ✅ App icon exists on your home screen
2. ✅ Opening app shows full-screen (no Safari UI)
3. ✅ window.navigator.standalone === true (in console)
4. ✅ Settings shows "Push notifications enabled"
5. ✅ Test notification appears on lock screen
6. ✅ iOS Settings shows "Nosana Monitor" in Notifications list
7. ✅ Real node status changes trigger notifications

---

## 📚 References

- [Apple: Sending Web Push Notifications](https://developer.apple.com/documentation/usernotifications/sending-web-push-notifications-in-web-apps-and-browsers)
- [iOS 16.4 Web Push Announcement](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/)
- [Firebase: Safari Web Push Support](https://firebase.blog/posts/2023/08/fcm-for-safari/)

---

**Last Updated:** October 18, 2024
**Your iOS Version:** 18.7.1 ✅
**App URL:** https://nosana-monitor.preview.emergentagent.com
**Key Requirement:** App MUST be installed to home screen!
