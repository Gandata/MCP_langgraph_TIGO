"""
Example usage of the Google Drive File Scanner

This script demonstrates how to use the GoogleDriveFileScanner class
to scan and catalog files from the 4 target folders.
"""

from data_loader.load_data_qdrant import GoogleDriveFileScanner
import json

def example_usage():
    """
    Example of how to use the Google Drive File Scanner
    """
    
    # Initialize the scanner
    scanner = GoogleDriveFileScanner()
    
    try:
        # Scan all target folders
        print("Starting Google Drive scan...")
        files_data = scanner.scan_target_folders()
        
        # Save to JSON file
        scanner.save_to_json(files_data, "my_drive_catalog.json")
        
        # Print summary
        scanner.print_summary(files_data)
        
        # Example: Access files from a specific folder
        print("\n=== EXAMPLE: Files in 'Transversal' folder ===")
        if 'Transversal' in files_data and files_data['Transversal']:
            for file_info in files_data['Transversal'][:5]:  # Show first 5 files
                print(f"Name: {file_info['name']}")
                print(f"Path: {file_info['path']}")
                print(f"Type: {file_info['type']}")
                print(f"Link: {file_info['webViewLink']}")
                print("-" * 50)
        else:
            print("No files found in 'Transversal' folder.")
            print("Make sure:")
            print("1. The folder is shared with your Google account")
            print("2. You have OAuth2 credentials set up (credentials.json)")
        
        # Example: Get all files (not folders) across all directories
        print("\n=== EXAMPLE: All files across directories ===")
        all_files = []
        for folder_name, files in files_data.items():
            files_only = [f for f in files if f.get('type') == 'file']
            all_files.extend(files_only)
        
        print(f"Total files found: {len(all_files)}")
        
        if all_files:
            # Example: Create a simple file dictionary by name
            file_dict = {file_info['name']: file_info['path'] for file_info in all_files}
            print(f"Created dictionary with {len(file_dict)} unique file names")
        else:
            print("\n⚠️  No files found. This usually means:")
            print("1. Folders are not shared with your Google account")
            print("2. OAuth2 authentication is required (see OAUTH2_SETUP.md)")
            print("3. Folder names might be different")
        
        return files_data, all_files, file_dict if all_files else {}
        
    finally:
        # Always clean up
        scanner.close()

if __name__ == "__main__":
    data, files, file_dict = example_usage()
