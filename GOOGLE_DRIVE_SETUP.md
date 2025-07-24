# Google Drive File Scanner Setup Guide

This guide will help you set up the Google Drive File Scanner to catalog files from your shared Google Drive folders.

## Prerequisites

1. **Google Cloud Project**: You need a Google Cloud project with the Google Drive API enabled.
2. **API Credentials**: Either an API key or OAuth2 credentials.

## Setup Steps

### Step 1: Install Dependencies

Run the following command to install the required packages:

```bash
uv sync
```

### Step 2: Google Cloud Console Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

### Step 3: Choose Authentication Method

#### Option A: API Key (Limited Access)

- Good for: Public files or files shared with "Anyone with the link"
- Limitations: Cannot access private shared files

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "API Key"
3. Copy the API key and add it to your `.env` file:
   ```
   GOOGLE_DRIVE_API_KEY=your_api_key_here
   ```

#### Option B: OAuth2 (Recommended)

- Good for: Full access to shared files
- Required for: Private shared folders

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Desktop Application"
4. Download the JSON file and rename it to `credentials.json`
5. Place `credentials.json` in your project root directory

### Step 4: Create Environment File

1. Copy `.env.example` to `.env`:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API key:
   ```
   GOOGLE_DRIVE_API_KEY=your_actual_api_key_here
   ```

### Step 5: Run the Scanner

#### Basic Usage:

```python
from data_loader.load_data_qdrant import GoogleDriveFileScanner

scanner = GoogleDriveFileScanner()
files_data = scanner.scan_target_folders()
scanner.save_to_json(files_data, "my_files.json")
scanner.print_summary(files_data)
```

#### Using the Example Script:

```bash
python example_drive_scan.py
```

## Output Structure

The scanner will create a JSON file with the following structure:

```json
{
  "Transversal": [
    {
      "id": "file_id",
      "name": "document.pdf",
      "mimeType": "application/pdf",
      "size": "1024",
      "modifiedTime": "2025-01-15T10:30:00.000Z",
      "webViewLink": "https://drive.google.com/file/d/...",
      "path": "Transversal/document.pdf",
      "parentFolder": "Transversal",
      "type": "file"
    }
  ],
  "Móvil": [...],
  "Fijo": [...],
  "Digital": [...]
}
```

## Data Structure Explanation

Each file entry contains:

- **id**: Google Drive file ID
- **name**: File name
- **mimeType**: File type (PDF, Word doc, etc.)
- **size**: File size in bytes
- **modifiedTime**: Last modification date
- **webViewLink**: Direct link to view the file
- **path**: Full path within the folder structure
- **parentFolder**: Main folder name
- **type**: Either "file" or "folder"

## Troubleshooting

### Common Issues:

1. **"Folder not found"**: The folder might not be shared with your account or the name is different.
2. **Authentication failed**: Check your API key or OAuth2 setup.
3. **Permission denied**: The folders might not be accessible with your current authentication method.

### Solutions:

1. **For shared folders**: Use OAuth2 authentication instead of API key.
2. **For folder names**: Check the exact folder names in Google Drive.
3. **For permissions**: Ensure the folders are shared with your Google account.

## Alternative Data Structures

Instead of the default nested structure, you can create:

### 1. Flat file dictionary:

```python
file_dict = {}
for folder_name, files in files_data.items():
    for file_info in files:
        if file_info['type'] == 'file':
            file_dict[file_info['name']] = file_info['path']
```

### 2. Grouped by file type:

```python
by_type = {}
for folder_name, files in files_data.items():
    for file_info in files:
        if file_info['type'] == 'file':
            mime_type = file_info['mimeType']
            if mime_type not in by_type:
                by_type[mime_type] = []
            by_type[mime_type].append(file_info)
```

### 3. Search-friendly format:

```python
searchable = []
for folder_name, files in files_data.items():
    for file_info in files:
        if file_info['type'] == 'file':
            searchable.append({
                'name': file_info['name'],
                'path': file_info['path'],
                'folder': folder_name,
                'link': file_info['webViewLink']
            })
```
