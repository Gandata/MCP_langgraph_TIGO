import os
import json
from typing import Dict, List, Optional
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Load environment variables
load_dotenv()

class GoogleDriveFileScanner:
    """
    A class to scan and catalog files in specific Google Drive folders.
    """
    
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_DRIVE_API_KEY')
        self.scopes = ['https://www.googleapis.com/auth/drive.readonly']
        self.service = None
        self.target_folders = ["Transversal", "Móvil", "Fijo", "Digital"]
        
    def authenticate(self):
        """
        Authenticate with Google Drive API using OAuth2 (for shared files) or API key fallback
        """
        try:
            # First try OAuth2 for shared files access
            if self._try_oauth2_auth():
                print("Authenticated using OAuth2 (can access shared files)")
                return
            
            # Fallback to API key (limited access)
            if self.api_key:
                self.service = build('drive', 'v3', developerKey=self.api_key)
                print("Authenticated using API key (limited access - public files only)")
            else:
                raise ValueError("No authentication method available. Need either OAuth2 credentials or API key.")
                
        except Exception as e:
            print(f"Authentication failed: {e}")
            raise
    
    def _try_oauth2_auth(self) -> bool:
        """
        Try OAuth2 authentication for accessing shared files
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            creds = None
            token_file = 'token.json'
            
            # Load existing token
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, self.scopes)
            
            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # Check if credentials.json exists
                    if not os.path.exists('credentials.json'):
                        print("credentials.json not found. OAuth2 authentication not available.")
                        print("For shared files access, you need to:")
                        print("1. Download credentials.json from Google Cloud Console")
                        print("2. Place it in the project root directory")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.scopes)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('drive', 'v3', credentials=creds)
            return True
            
        except Exception as e:
            print(f"OAuth2 authentication failed: {e}")
            return False
    
    def find_folder_by_name(self, folder_name: str) -> Optional[str]:
        """
        Find a folder by name in Google Drive
        
        Args:
            folder_name (str): Name of the folder to find
            
        Returns:
            Optional[str]: Folder ID if found, None otherwise
        """
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, parents)',
                pageSize=100
            ).execute()
            
            folders = results.get('files', [])
            if folders:
                return folders[0]['id']  # Return the first match
            return None
            
        except Exception as e:
            print(f"Error finding folder '{folder_name}': {e}")
            return None
    
    def list_files_in_folder(self, folder_id: str, folder_name: str = "") -> List[Dict]:
        """
        Recursively list all files in a folder
        
        Args:
            folder_id (str): Google Drive folder ID
            folder_name (str): Name of the folder (for path building)
            
        Returns:
            List[Dict]: List of file information dictionaries
        """
        files_list = []
        
        try:
            # Query for all items in the folder
            query = f"'{folder_id}' in parents and trashed=false"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType, parents, size, modifiedTime, webViewLink)',
                pageSize=1000
            ).execute()
            
            items = results.get('files', [])
            
            for item in items:
                file_info = {
                    'id': item['id'],
                    'name': item['name'],
                    'mimeType': item['mimeType'],
                    'size': item.get('size', 'N/A'),
                    'modifiedTime': item.get('modifiedTime', 'N/A'),
                    'webViewLink': item.get('webViewLink', 'N/A'),
                    'path': f"{folder_name}/{item['name']}" if folder_name else item['name'],
                    'parentFolder': folder_name
                }
                
                # If it's a folder, recursively get its contents
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    file_info['type'] = 'folder'
                    files_list.append(file_info)
                    
                    # Recursively scan subfolder
                    subfolder_path = f"{folder_name}/{item['name']}" if folder_name else item['name']
                    subfiles = self.list_files_in_folder(item['id'], subfolder_path)
                    files_list.extend(subfiles)
                else:
                    file_info['type'] = 'file'
                    files_list.append(file_info)
                    
        except Exception as e:
            print(f"Error listing files in folder '{folder_name}': {e}")
            
        return files_list
    
    def scan_target_folders(self) -> Dict[str, List[Dict]]:
        """
        Scan all target folders and return organized file information
        
        Returns:
            Dict[str, List[Dict]]: Dictionary with folder names as keys and file lists as values
        """
        if not self.service:
            self.authenticate()
        
        all_files = {}
        
        for folder_name in self.target_folders:
            print(f"Scanning folder: {folder_name}")
            
            folder_id = self.find_folder_by_name(folder_name)
            if folder_id:
                files = self.list_files_in_folder(folder_id, folder_name)
                all_files[folder_name] = files
                print(f"Found {len(files)} items in '{folder_name}'")
            else:
                print(f"Folder '{folder_name}' not found or not accessible")
                all_files[folder_name] = []
        
        return all_files
    
    def save_to_json(self, data: Dict, filename: str = "google_drive_files.json"):
        """
        Save the file information to a JSON file
        
        Args:
            data (Dict): File information dictionary
            filename (str): Output filename
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"File information saved to {filename}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")
    
    def print_summary(self, data: Dict):
        """
        Print a summary of the scanned files
        
        Args:
            data (Dict): File information dictionary
        """
        print("\n=== GOOGLE DRIVE SCAN SUMMARY ===")
        total_files = 0
        total_folders = 0
        
        for folder_name, files in data.items():
            files_count = len([f for f in files if f.get('type') == 'file'])
            folders_count = len([f for f in files if f.get('type') == 'folder'])
            
            print(f"\n{folder_name}:")
            print(f"  - Files: {files_count}")
            print(f"  - Folders: {folders_count}")
            print(f"  - Total items: {len(files)}")
            
            total_files += files_count
            total_folders += folders_count
        
        print(f"\nGRAND TOTAL:")
        print(f"  - Files: {total_files}")
        print(f"  - Folders: {total_folders}")
        print(f"  - Total items: {total_files + total_folders}")
    
    def close(self):
        """
        Close the Google Drive service connection
        """
        if self.service:
            self.service.close()


def main():
    """
    Main function to execute the Google Drive file scanning
    """
    scanner = None
    try:
        scanner = GoogleDriveFileScanner()
        
        # Scan all target folders
        files_data = scanner.scan_target_folders()
        
        # Save to JSON file
        scanner.save_to_json(files_data, "google_drive_catalog.json")
        
        # Print summary
        scanner.print_summary(files_data)
        
        return files_data
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        return None
    finally:
        # Clean up resources
        if scanner:
            scanner.close()


if __name__ == "__main__":
    result = main()