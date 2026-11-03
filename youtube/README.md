# GitHub → YouTube Auto Upload

`youtube/videos/` में `.mp4` push करते ही GitHub Actions उसे YouTube पर अपने आप upload कर देगा।

## एक बार का सेटअप

1. **Google Cloud Console** → APIs & Services:
   - **YouTube Data API v3** को Enable करें।
   - Credentials → अपना OAuth client खोलें → Authorized redirect URIs में `http://localhost:8080/` जोड़ें।
   - OAuth consent screen → Test users में अपना YouTube वाला Gmail जोड़ें, फिर app को **Publish (In production)** करें। Testing mode में token 7 दिन में expire हो जाता है।
2. PC पर refresh token निकालें:
   ```
   pip install google-auth-oauthlib
   python youtube/get_token.py "C:\Users\Admin\Downloads\client_secret_....json"
   ```
   Browser में login करें और channel चुनें।
3. GitHub repo → Settings → Secrets and variables → Actions में ये तीन secrets बनाएँ:
   `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`

## रोज़ का इस्तेमाल

```
youtube/videos/percentage.mp4
youtube/videos/percentage.json
```
```json
{
  "title": "प्रतिशत | SSC CGL PYQ ट्रिक",
  "description": "...",
  "tags": ["SSC", "Percentage", "प्रतिशत"],
  "privacy": "public",
  "publish_at": "2026-11-10T06:00:00Z"
}
```
`git add`, `commit`, `push` करें। Upload हो जाने के बाद link `youtube/uploaded.json` में आ जाता है और वही video दोबारा upload नहीं होता।

**सीमाएँ:** GitHub पर एक file 100 MB से बड़ी नहीं हो सकती। बड़ी video के लिए `git lfs track "*.mp4"` चलाएँ। API quota के हिसाब से एक दिन में लगभग 6 uploads ही हो पाते हैं।
