#!/usr/bin/env python3
"""
Test script for verifying service account setup and permissions.
Run this before using the main load_drive_documents.py script.
"""

import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = ['https://www.googleapis.com/auth/drive']

def test_service_account_setup():
    """Test if service account is properly configured"""
    
    print("🔍 Testing Service Account Setup...")
    print("=" * 50)
    
    # Check if service account file exists
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print("❌ Service account file not found!")
        print(f"   Expected file: {SERVICE_ACCOUNT_FILE}")
        print("   Please follow the setup instructions in README_SERVICE_ACCOUNT.md")
        return False
    
    print("✅ Service account file found")
    
    # Load and validate service account file
    try:
        with open(SERVICE_ACCOUNT_FILE, 'r') as f:
            service_account_info = json.load(f)
        
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in service_account_info]
        
        if missing_fields:
            print(f"❌ Service account file is missing required fields: {missing_fields}")
            return False
        
        if service_account_info.get('type') != 'service_account':
            print("❌ Invalid service account file - type should be 'service_account'")
            return False
            
        print("✅ Service account file is valid")
        print(f"   Service Account Email: {service_account_info['client_email']}")
        print(f"   Project ID: {service_account_info['project_id']}")
        
    except json.JSONDecodeError:
        print("❌ Service account file contains invalid JSON")
        return False
    except Exception as e:
        print(f"❌ Error reading service account file: {e}")
        return False
    
    # Test authentication
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        print("✅ Service account credentials loaded successfully")
        
    except Exception as e:
        print(f"❌ Error loading service account credentials: {e}")
        return False
    
    # Test Drive API access
    try:
        drive_service = build('drive', 'v3', credentials=credentials)
        print("✅ Google Drive API service initialized successfully")
        
        # Test basic API call (list user's drive - this should work even without shared drive access)
        about = drive_service.about().get(fields='user').execute()
        print(f"✅ API connection successful - authenticated as: {about.get('user', {}).get('emailAddress', 'Unknown')}")
        
    except HttpError as e:
        if e.resp.status == 403:
            print("❌ API access denied - check if Google Drive API is enabled in your project")
        else:
            print(f"❌ HTTP Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error connecting to Google Drive API: {e}")
        return False
    
    print("\n🎉 Service account setup is working correctly!")
    print("\nNext steps:")
    print("1. Get the Shared Drive ID from the Google Drive URL")
    print("2. Grant the service account access to the shared drive:")
    print(f"   Add this email as a member: {service_account_info['client_email']}")
    print("3. Run load_drive_documents.py to access the shared drive")
    
    return True

def test_shared_drive_access(shared_drive_id):
    """Test access to a specific shared drive"""
    
    print(f"\n🔍 Testing access to Shared Drive: {shared_drive_id}")
    print("=" * 50)
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # Try to list files in the shared drive
        results = drive_service.files().list(
            q=f"'{shared_drive_id}' in parents and trashed=false",
            spaces='drive',
            corpora='drive',
            driveId=shared_drive_id,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields="files(id, name, mimeType)",
            pageSize=10
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            print(f"✅ Successfully accessed shared drive!")
            print(f"   Found {len(files)} files (showing first 10):")
            for file in files[:10]:
                print(f"   - {file['name']} ({file['mimeType']})")
        else:
            print("✅ Successfully accessed shared drive, but no files found")
            
        return True
        
    except HttpError as e:
        if e.resp.status == 404:
            print("❌ Shared drive not found or service account doesn't have access")
            print("   This usually means:")
            print("   1. The ID provided is NOT a shared drive ID (it might be a regular folder)")
            print("   2. The shared drive doesn't exist")
            print("   3. The service account email has not been added as a member")
            print("\n   🔍 DEBUGGING INFO:")
            print(f"   Error details: {e}")
            print(f"   Response status: {e.resp.status}")
            
            # Try to determine if it's a regular folder instead
            print("\n   💡 Let's check if this is a regular shared folder instead...")
            return test_regular_folder_access(shared_drive_id, drive_service)
            
        elif e.resp.status == 403:
            print("❌ Access denied to shared drive")
            print("   Make sure the service account email has been added as a member of the shared drive")
        else:
            print(f"❌ HTTP Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error accessing shared drive: {e}")
        return False

def test_regular_folder_access(folder_id, drive_service):
    """Test access to a regular shared folder"""
    
    print(f"\n🔍 Testing access as regular folder: {folder_id}")
    print("-" * 30)
    
    try:
        # Try to get folder information first
        folder_info = drive_service.files().get(
            fileId=folder_id,
            fields="id, name, mimeType, owners, permissions"
        ).execute()
        
        print(f"✅ Found folder: '{folder_info['name']}'")
        print(f"   Type: {folder_info['mimeType']}")
        
        if folder_info['mimeType'] == 'application/vnd.google-apps.folder':
            # Try to list files in the folder
            results = drive_service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="files(id, name, mimeType)",
                pageSize=10
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                print(f"✅ Successfully accessed folder!")
                print(f"   Found {len(files)} files (showing first 10):")
                for file in files[:10]:
                    print(f"   - {file['name']} ({file['mimeType']})")
            else:
                print("✅ Successfully accessed folder, but no files found")
            
            print(f"\n   📝 NOTE: This is a REGULAR FOLDER, not a SHARED DRIVE")
            print(f"   For regular folders, use the updated main script that handles both types.")
            return True
        else:
            print(f"❌ This is not a folder, it's a {folder_info['mimeType']}")
            return False
            
    except HttpError as e:
        if e.resp.status == 404:
            print("❌ Folder not found")
        elif e.resp.status == 403:
            print("❌ Access denied to folder")
            print("   Make sure the folder is shared with the service account email")
        else:
            print(f"❌ HTTP Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error accessing folder: {e}")
        return False

def explain_drive_types():
    """Explain the difference between shared drives and shared folders"""
    
    print("\n" + "=" * 60)
    print("📚 UNDERSTANDING GOOGLE DRIVE TYPES")
    print("=" * 60)
    
    print("\n🏢 SHARED DRIVE (formerly Team Drive):")
    print("   - Belongs to an organization, not an individual")
    print("   - URL looks like: https://drive.google.com/drive/folders/SHARED_DRIVE_ID")
    print("   - Requires special API parameters (driveId, includeItemsFromAllDrives)")
    print("   - Members are managed at the shared drive level")
    print("   - Service account must be added as a member of the entire shared drive")
    
    print("\n📁 SHARED FOLDER (regular folder):")
    print("   - Regular folder that someone shared with you")
    print("   - URL looks like: https://drive.google.com/drive/folders/FOLDER_ID")
    print("   - Uses standard Drive API calls")
    print("   - Sharing is managed at the folder level")
    print("   - Service account must be granted access to the specific folder")
    
    print("\n❓ HOW TO TELL THE DIFFERENCE:")
    print("   1. If you see 'Shared drives' in the left sidebar → Shared Drive")
    print("   2. If you see 'Shared with me' in the left sidebar → Shared Folder")
    print("   3. Shared drives typically have organization names")
    print("   4. Shared folders show the owner's name")
    
    print("\n💡 BOTH WORK with this script - it will auto-detect the type!")
    print("=" * 60)

if __name__ == "__main__":
    print("🔧 Google Drive Service Account Test Tool")
    print("=" * 50)
    
    # Test basic setup
    if not test_service_account_setup():
        print("\n❌ Setup test failed. Please fix the issues above before continuing.")
        exit(1)
    
    # Show explanation of drive types
    explain_drive_types()
    
    # Ask if user wants to test shared drive access
    print("\n" + "=" * 50)
    test_drive = input("Do you want to test access to a Drive ID? (y/n): ").lower().strip()
    
    if test_drive == 'y':
        drive_id = input("Enter the Drive/Folder ID: ").strip()
        if drive_id:
            test_shared_drive_access(drive_id)
        else:
            print("❌ No Drive/Folder ID provided")
    
    print("\n✨ Test completed!")
