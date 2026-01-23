# YouTube Bot Detection Issue

## Problem
YouTube blocks yt-dlp on server environments (like Render) by detecting automated access. You'll see errors like:
```
Sign in to confirm you're not a bot
```

## Current Mitigations (Already Implemented)

### 1. Android Player Client
We use YouTube's Android player client which is less likely to be blocked:
```python
"player_client": ["android", "web"]
```

### 2. Proper User Agent
We spoof a real browser user agent to look less like a bot.

### 3. Graceful Degradation
If video download fails:
- Recipe extraction still works from description/comments
- User gets a helpful error message suggesting alternatives

## Optional: Add YouTube Cookies (More Reliable)

If you continue experiencing bot detection, you can add YouTube cookies:

### Step 1: Export Cookies from Browser

**Option A: Using Browser Extension**
1. Install "Get cookies.txt LOCALLY" extension (Firefox/Chrome)
2. Go to youtube.com and log in
3. Click the extension and export cookies
4. Save as `youtube_cookies.txt`

**Option B: Manual Export**
Follow guide: https://github.com/yt-dlp/yt-dlp/wiki/Extractors#exporting-youtube-cookies

### Step 2: Add to Render

1. Upload `youtube_cookies.txt` to a private location (or use secrets management)
2. In Render dashboard, add environment variable:
   ```
   YOUTUBE_COOKIES_PATH=/path/to/youtube_cookies.txt
   ```

### Step 3: Deploy
The application will automatically use cookies if `YOUTUBE_COOKIES_PATH` is set.

## Trade-offs

| Method | Pros | Cons |
|--------|------|------|
| **No cookies (current)** | • No maintenance<br>• No personal data<br>• Works for most videos | • May fail on some videos<br>• Can't access private/age-restricted content |
| **With cookies** | • More reliable<br>• Access age-restricted content<br>• Bypasses most bot detection | • Requires Google account<br>• Cookies expire (~6 months)<br>• Requires maintenance |

## Recommendations

1. **Start without cookies** - Most recipes are in descriptions/comments anyway
2. **Add cookies only if needed** - If you frequently hit bot detection
3. **Consider alternatives** - Ask users to paste recipe from description

## Testing

Test the YouTube video extraction:
```bash
curl -X POST http://localhost:8000/api/extract-recipe \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/shorts/xe6gvF2nYoI"}'
```

Expected behavior:
- ✅ Extracts from description/comments if available
- ⚠️  Shows friendly error if video download is blocked
- ❌ Does NOT crash the application
