# Lock Screen Notifications - Setup Guide

## 🔔 Overview
Push notifications will now appear on your lock screen, light up your phone, and alert you immediately when your nodes need attention - even when the app is closed!

## ✅ What's Been Fixed

### **Before:**
- ❌ Notifications only appeared when app was open
- ❌ No lock screen display
- ❌ Screen didn't light up
- ❌ Had to unlock phone to see notifications

### **After:**
- ✅ Notifications appear on lock screen
- ✅ Screen lights up automatically
- ✅ Strong vibration pattern (300ms-100ms-300ms-100ms-300ms)
- ✅ Sound plays (if enabled in settings)
- ✅ Works even when app is completely closed
- ✅ High priority delivery

## 📱 How It Works Now

### **Notification Behavior:**

**When Node Goes Offline:**
1. Screen lights up immediately
2. Shows notification on lock screen
3. Vibrates with custom pattern
4. Plays notification sound
5. Stays visible until you check it

**Lock Screen Display:**
```
🔴 Node Went Offline
Your Perf Test Node 0 is now OFFLINE
[Open App] [Dismiss]
```

**Notification Details:**
- **Title**: Clear alert (e.g., "🔴 Node Went Offline")
- **Body**: Specific node name and issue
- **Icon**: Nosana logo
- **Actions**: "Open App" or "Dismiss"
- **Priority**: HIGH (ensures delivery)
- **Visibility**: PUBLIC (shows on lock screen)

## 🔧 Technical Implementation

### **Service Worker Enhancements:**
- Configured for background message handling
- High priority notification delivery
- Lock screen visibility
- Custom vibration patterns
- Sound enabled by default

### **Backend Configuration:**

**Android:**
- Priority: HIGH
- Visibility: PUBLIC (lock screen)
- Sound: Default notification sound
- Vibration: [300, 100, 300, 100, 300] ms
- Notification Priority: PRIORITY_HIGH

**iOS (iPhone):**
- APNS Priority: 10 (maximum)
- Content Available: True (wakes device)
- Sound: Enabled
- Badge: Shows count

**PWA (Web):**
- RequireInteraction: False (auto-dismiss)
- Renotify: True (alert each time)
- Tag: Groups similar notifications
- Vibrate: Enabled

## 📋 User Requirements

### **For Best Results, Users Should:**

**1. Install App to Home Screen (PWA)**
- Open app in browser
- Tap "Add to Home Screen"
- Notifications work better when installed

**2. Grant Notification Permission**
- In app: Go to Settings (⚙️ icon)
- Tap "Enable Notifications"
- Allow when prompted

**3. Enable Permissions in Phone Settings**

**Android:**
```
Settings → Apps → Nosana Monitor
→ Notifications → Allow
→ Lock screen → Show all notification content
→ Priority → Set to High
```

**iOS (iPhone):**
```
Settings → Notifications → Nosana Monitor
→ Allow Notifications: ON
→ Lock Screen: ON
→ Banner Style: Persistent
→ Sounds: ON
→ Show Previews: Always
```

## 🎯 Notification Types

**Critical Alerts (Lock Screen + Light Up):**
- 🔴 Node Went Offline
- ✅ Node Back Online
- 🚀 Job Started
- ✅ Job Completed

**All Include:**
- Node name/identifier
- Timestamp
- Quick action buttons
- Direct link to app

## 🔊 Sound & Vibration

**Default Settings:**
- ✅ Sound: Enabled (default notification sound)
- ✅ Vibration: Enabled (custom pattern)

**User Control:**
Users can customize in app settings:
- Settings → Notifications → Sound (ON/OFF)
- Settings → Notifications → Vibration (ON/OFF)

**Vibration Pattern:**
```
300ms vibrate
100ms pause
300ms vibrate
100ms pause
300ms vibrate
= Strong, noticeable alert
```

## 🧪 Testing

**To Test Notifications:**
1. Log in to app
2. Go to Settings (⚙️)
3. Enable Notifications
4. Tap "Send Test Notification"
5. **Lock your phone**
6. Notification should:
   - Light up screen
   - Show on lock screen
   - Vibrate
   - Play sound

**If It Doesn't Work:**
- Check phone notification permissions
- Ensure app is installed as PWA
- Check "Do Not Disturb" mode is off
- Verify notification settings in app

## 📊 Priority Levels

**HIGH Priority (Current):**
- ✅ Bypasses battery optimization
- ✅ Shows on lock screen
- ✅ Lights up screen
- ✅ Plays sound
- ✅ Vibrates strongly
- ✅ Delivered immediately

**What This Means:**
- Notifications treated like SMS/calls
- Won't be delayed or grouped
- Always visible
- Can't be silenced by apps
- Requires explicit user dismiss

## 🔒 Privacy & Lock Screen

**What Shows on Lock Screen:**
- Notification title
- Notification body
- App icon
- Action buttons

**What Doesn't Show:**
- Sensitive node addresses (shortened)
- Account details
- Balances

**Privacy Options:**
If users want privacy on lock screen:
```
Phone Settings → Security/Privacy
→ Lock screen → Hide sensitive content
```
(Notifications still alert, but content hidden)

## ⚠️ Important Notes

### **Battery Impact:**
- HIGH priority notifications may use slightly more battery
- Necessary for reliable lock screen alerts
- Users can adjust in phone settings if needed

### **Do Not Disturb Mode:**
- System DND may still block notifications
- Users should add Nosana Monitor to "Priority apps" list
- Or disable DND for critical node monitoring

### **Browser Limitations:**
- **Best**: Installed as PWA (home screen)
- **Good**: Chrome/Safari with notifications enabled
- **Limited**: Some browsers restrict background notifications

### **Recommended Setup:**
1. Install app to home screen (PWA)
2. Enable notifications in app
3. Grant all permissions when prompted
4. Add to "Priority apps" in phone settings
5. Test with "Send Test Notification"

## 🎉 Result

**Users will now get:**
- ✅ Immediate alerts on lock screen
- ✅ Screen lights up for important events
- ✅ Strong vibration to grab attention
- ✅ Sound notification
- ✅ Quick access to app via notification
- ✅ Never miss a node going offline!

## 📱 Platform-Specific Behavior

### **Android:**
- Lock screen: Full notification with actions
- Banner: Heads-up notification
- Sound: Plays immediately
- Vibration: Custom pattern
- LED: May flash if phone supports it

### **iOS (iPhone):**
- Lock screen: Banner notification
- Banner: Top banner slide-down
- Sound: Plays immediately
- Vibration: Enabled
- Badge: Shows count on app icon

### **Desktop (PWA):**
- System notification tray
- Sound plays
- Click to open app
- Persists until dismissed

---

**Last Updated**: October 18, 2025
**Status**: ✅ Active - HIGH Priority Notifications Enabled
**Test Command**: Use "Send Test Notification" in Settings
