# PWA Auto-Update System

## Overview
The Nosana Node Monitor app now includes an automatic update system that allows users to receive new features and bug fixes without reinstalling the app.

## How It Works

### 1. Service Worker
- **File**: `/app/frontend/public/service-worker.js`
- **Version**: Managed via `CACHE_VERSION` constant
- **Strategy**: Network-first for API calls, cache-first for static assets

### 2. Update Detection
- App checks for updates every 60 seconds
- When a new version is deployed, users see:
  - Toast notification: "New version available! Tap to update."
  - Green "Update Available" button in the header

### 3. Update Process
1. User clicks "Update Now" or "Update Available" button
2. New service worker takes control
3. Page reloads automatically with new version
4. User sees updated features immediately

## For Developers

### Deploying Updates

**Step 1: Update the service worker version**
```javascript
// In /app/frontend/public/service-worker.js
const CACHE_VERSION = 'v1.0.1'; // Increment this!
```

**Step 2: Update version.json** (optional but recommended)
```json
{
  "version": "1.0.1",
  "buildDate": "2025-10-18",
  "changes": [
    "Your change description here"
  ]
}
```

**Step 3: Deploy**
```bash
# Frontend hot-reloads automatically
# Or restart if needed:
sudo supervisorctl restart frontend
```

**That's it!** Users will get an update notification within 60 seconds.

### Version Numbering
- **Major**: Breaking changes (2.0.0)
- **Minor**: New features (1.1.0)
- **Patch**: Bug fixes (1.0.1)

### Cache Strategy

**Network First (API calls):**
- `/api/*` - Always try network first
- Falls back to cache if offline
- Updates cache with fresh data

**Cache First (Static assets):**
- HTML, CSS, JS, images
- Returns cached version immediately
- Updates cache in background

**Navigate (HTML pages):**
- Always tries network first
- Falls back to cache if offline
- Ensures users get latest version

## For Users

### How to Update

**Automatic (Recommended):**
1. Keep the app open
2. When you see "Update Available" button, tap it
3. App updates automatically

**Manual:**
1. Close the app completely
2. Reopen it
3. New version loads automatically

### If Updates Don't Work

**Option 1: Force Reload**
- On phone: Close app, reopen
- In browser: Ctrl+Shift+R (hard reload)

**Option 2: Clear Cache** (rare cases)
1. Go to phone Settings
2. Apps → Nosana Monitor
3. Storage → Clear Cache
4. Reopen app

**Option 3: Reinstall** (last resort)
- Only needed if major breaking changes
- Will be communicated in advance

## Technical Details

### Cache Lifecycle
1. **Install**: New service worker caches essential files
2. **Activate**: Old caches are deleted, new cache takes over
3. **Fetch**: Serves requests from cache/network based on strategy
4. **Update**: Checks for new service worker, notifies user

### Update Frequency
- **Check interval**: Every 60 seconds
- **User action required**: Yes (tap "Update Now")
- **Automatic reload**: Yes (after user confirms)

### Offline Support
- App works offline after first visit
- Cached data available when no internet
- API calls fail gracefully
- Updates require internet connection

## Troubleshooting

### "Update Available" button not showing?
- Wait 60 seconds after deployment
- Check browser console for errors
- Try hard reload: Ctrl+Shift+R

### App still showing old version?
- Make sure service worker version was updated
- Check: `/service-worker.js?v=timestamp`
- Clear browser cache
- Check browser dev tools → Application → Service Workers

### Service worker not registering?
- Check browser console for errors
- Verify `/service-worker.js` is accessible
- Check HTTPS is enabled (required for service workers)

## Browser Support
- ✅ Chrome (Desktop & Mobile)
- ✅ Safari (iOS 11.3+)
- ✅ Firefox
- ✅ Edge
- ✅ Samsung Internet
- ❌ IE11 (not supported)

## Best Practices

### For Smooth Updates:
1. **Increment version** in service-worker.js
2. **Test locally** before deploying
3. **Update version.json** for tracking
4. **Communicate** major changes to users
5. **Monitor** update adoption in analytics

### For Breaking Changes:
1. **Increment major version** (2.0.0)
2. **Add migration logic** if needed
3. **Communicate** with users in advance
4. **Consider** prompting reinstall for major updates

## Monitoring

### Check Update Status
```javascript
// In browser console
navigator.serviceWorker.getRegistrations().then(regs => {
  console.log('Service Workers:', regs);
});
```

### Check Cache Status
```javascript
// In browser console
caches.keys().then(names => {
  console.log('Caches:', names);
});
```

### Clear All Caches (Development)
```javascript
// In browser console
caches.keys().then(names => {
  names.forEach(name => caches.delete(name));
});
```

## Version History

### v1.0.1 (Oct 18, 2025)
- ✅ Added auto-update mechanism
- ✅ Addresses/balances visible by default
- ✅ Fixed job started notifications
- ✅ Improved PWA caching

### v1.0.0 (Oct 17, 2025)
- Initial release
- Node monitoring
- Push notifications
- Multiple themes

---

**Last Updated**: October 18, 2025
**Status**: ✅ Active
**Auto-Updates**: ✅ Enabled
