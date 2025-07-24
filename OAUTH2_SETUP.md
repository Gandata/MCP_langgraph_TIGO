# Quick OAuth2 Setup for Shared Files Access

## The Problem

API keys cannot access shared Google Drive files. You need OAuth2 authentication to access files that have been shared with you.

## Quick Setup Steps

### 1. Get OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create one)
3. Enable the Google Drive API:

   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

4. Create OAuth2 credentials:

   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop Application"
   - Download the JSON file

5. **Rename the downloaded file to `credentials.json`**
6. **Place `credentials.json` in your project root directory** (same folder as `pyproject.toml`)

### 2. Install Dependencies

```bash
uv sync
```

### 3. Run Your Scanner

```bash
python example_drive_scan.py
```

**First time:** The script will open your browser for authorization. Log in with the Google account that has access to the shared folders.

**After authorization:** A `token.json` file will be saved for future use.

## What Happens Now

✅ **OAuth2 First**: Tries to access shared files  
✅ **API Key Fallback**: Falls back to API key if OAuth2 fails  
✅ **Automatic Token Refresh**: Handles token expiration automatically  
✅ **One-time Setup**: Browser auth only needed once

## File Structure

```
your-project/
├── credentials.json     # OAuth2 credentials (you download this)
├── token.json          # Saved tokens (auto-generated)
├── .env               # Your API key
└── data_loader/
    └── load_data_qdrant.py
```

## Why This Works

- **API Key**: Limited to public files only
- **OAuth2**: Can access shared files with your permission
- **Your Use Case**: Shared folders require OAuth2

The script now intelligently tries OAuth2 first (for shared access), then falls back to API key if needed.
