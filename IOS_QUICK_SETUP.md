# 🍎 iOS Quick Setup: 5 Steps to Enable Notifications

## The Problem
You're trying to enable notifications on iOS but they don't appear. This is because **iOS requires the app to be installed to your home screen** for notifications to work.

## The Solution: 5 Easy Steps

### Step 1: Open in Safari 🌐
- Current URL: https://node-pulse.preview.emergentagent.com
- **Must use Safari** (not Chrome or other browsers)
- You're probably already here!

### Step 2: Tap Share Button 📤
- Look at the **bottom of Safari**
- Tap the **share icon** (square with arrow pointing up)
- A menu will slide up from the bottom

### Step 3: Add to Home Screen 📱
- In the share menu, **scroll down**
- Find and tap **"Add to Home Screen"**
- You'll see:
  - App icon (green Nosana logo)
  - App name: "Nosana Monitor"
- Tap **"Add"** in the top right corner
- Safari will close

### Step 4: Open from Home Screen Icon 🏠
- Go to your **home screen**
- Find the **"Nosana Monitor" icon** (green logo)
- **Tap the icon** to open the app
- ⚠️ **Important**: Open from home screen, NOT from Safari!

### Step 5: Enable Notifications 🔔
Now that the app is installed:

1. **Login** to your account (if not already logged in)

2. **Tap Settings icon** (⚙️ gear icon in top right)

3. **You'll see a yellow warning box**:
   - If you still see it, you opened from Safari instead of home screen
   - Go back and open from the home screen icon!

4. **If no yellow warning**, tap **"Enable Notifications"**

5. **iOS will ask for permission** - Tap **"Allow"**

6. **Success!** You'll see: "🎉 Push notifications enabled!"

7. **Tap "Send Test Notification"** to test

8. **Lock your phone** - notification should appear!

---

## Visual Checklist

### ✅ You're doing it right if:
- App icon exists on home screen
- Opening app shows full screen (no Safari browser UI)
- Settings modal shows "Enable Notifications" button (no yellow warning)
- After enabling, you see "✅ Push notifications are enabled"

### ❌ You're doing it wrong if:
- Opening app in Safari browser (URL bar visible at top/bottom)
- Yellow warning about iOS appears in Settings
- Can't find "Add to Home Screen" option (you're not in Safari)
- App doesn't have an icon on home screen

---

## Troubleshooting

### "I don't see Add to Home Screen"
- Make sure you're in **Safari** (not Chrome/Firefox)
- Tap the **Share** button (not the tab switcher)
- **Scroll down** in the share menu - it's below the apps

### "I added it but still see the warning"
- Did you open from the **home screen icon**?
- Or are you still in Safari?
- Close Safari completely
- Go to home screen
- Tap the Nosana Monitor icon

### "Permission dialog doesn't appear"
- Settings → Nosana Monitor → Notifications
- Toggle "Allow Notifications" ON
- Return to app and try again

### "Test notification doesn't appear"
- Lock your phone immediately after sending test
- Check: Settings → Nosana Monitor → Notifications → Lock Screen is ON
- Turn off Focus modes
- Turn off Do Not Disturb

---

## Why iOS is Different

| Feature | Android/Desktop | iOS |
|---------|----------------|-----|
| Browser support | Chrome, Firefox, Edge, Safari | Safari only |
| Installation required | No (nice to have) | **YES (required!)** |
| In-browser notifications | ✅ Works | ❌ Doesn't work |
| PWA notifications | ✅ Works | ✅ Works (when installed) |

**iOS design choice**: Apple requires apps to be installed before allowing notifications. This prevents random websites from spamming you with notification requests.

---

## After Setup

Once you've completed all 5 steps:

1. **Configure what to get notified about:**
   - Node offline alerts
   - Node online alerts
   - Job started alerts
   - Job completed alerts

2. **Enable sound and vibration**

3. **Save preferences**

4. **Add your nodes** (if you haven't already)

5. **Notifications will arrive automatically** when node status changes!

---

## Quick Test

Run this in Safari dev tools (if you have a Mac):

```javascript
console.log('iOS:', /iPad|iPhone|iPod/.test(navigator.userAgent));
console.log('Standalone:', window.navigator.standalone);
console.log('Should be: iOS: true, Standalone: true');
```

- `iOS: true` = You're on iOS ✅
- `Standalone: true` = App is installed ✅
- `Standalone: false` = Not installed, follow steps above! ❌

---

## Need More Help?

See the complete guide: `/app/IOS_NOTIFICATION_GUIDE.md`

Or contact support with:
- Your iOS version (you have 18.7.1)
- Screenshots of Settings modal
- Any error messages in console

---

**Key Takeaway**: On iOS, you MUST install the app to your home screen for notifications to work. Regular Safari browsing doesn't support web push notifications!

Good luck! 🍀
