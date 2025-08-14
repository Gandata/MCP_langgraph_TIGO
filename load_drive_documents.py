#Ver todos los documentos en la carpetas compartidas de Google Drive
import os
import io
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = ['https://www.googleapis.com/auth/drive']
local_path = os.path.join(os.getcwd(), "exports")

if not os.path.exists(local_path):
    os.makedirs(local_path)

def get_service_account_credentials():
    """
    Create credentials using service account file
    """
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
    
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return credentials

def get_service_account_email():
    """
    Get the email address of the service account from the service account file.
    This email needs to be granted access to the shared drive.
    """
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
    
    with open(SERVICE_ACCOUNT_FILE, 'r') as f:
        service_account_info = json.load(f)
    
    return service_account_info.get('client_email')

def sanitize_filename(filename):
    # Replace slashes and other problematic characters
    filename = filename.replace('<', '-').replace('>', '-').replace(':', '-').replace('"', '-').replace('/', '-').replace('\\', '-').replace('|', '-').replace('?', '-').replace('*', '-').replace('(', '-').replace(')', '-').replace(',', '-')
    filename = (filename[:255]) if len(filename) > 255 else filename
    return filename

def download_file(drive_service, file_id, file_name, local_folder_path, mime_type):
    file_name = sanitize_filename(file_name)

    # Mapping for Google Drive document types to Microsoft Office formats
    google_mime_map = {
        'application/vnd.google-apps.document': ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx'),
        'application/vnd.google-apps.spreadsheet': ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx'),
        'application/vnd.google-apps.presentation': ('application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx'),
    }

    # Check if the file is a Google Docs type and needs conversion
    if mime_type in google_mime_map:
        mime_type_export, file_extension = google_mime_map[mime_type]
        request = drive_service.files().export_media(fileId=file_id, mimeType=mime_type_export)
    else:
        # Handle existing Microsoft Office files and other types
        if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            file_extension = '.docx'
        elif mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            file_extension = '.xlsx'
        elif mime_type == 'application/vnd.openxmlformats-officedocument.presentationml.presentation':
            file_extension = '.pptx'
        else:
            file_extension = '.' + mime_type.split('/')[-1].split(';')[0] if '/' in mime_type else '.bin'
        
        request = drive_service.files().get_media(fileId=file_id)
    
    # Remove any existing extension from the file name
    file_name = os.path.splitext(file_name)[0]
    
    # Append the correct file extension
    file_name += file_extension
    
    file_path_with_extension = os.path.join(local_folder_path, file_name)
    os.makedirs(os.path.dirname(file_path_with_extension), exist_ok=True)

    # Check if the file already exists locally
    if os.path.exists(file_path_with_extension):
        print(f"File already exists, skipping download: {file_path_with_extension}")
        return  # Skip download if file exists

    try:
        file_data = io.BytesIO()
        downloader = MediaIoBaseDownload(file_data, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

        with open(file_path_with_extension, 'wb') as f:
            f.write(file_data.getvalue())
        print(f"File saved: {file_path_with_extension}")
    except Exception as e:
        print(f"Failed to download {file_name}. Error: {str(e)}")


def detect_drive_type(drive_service, drive_id):
    """
    Detect if the given ID is a shared drive or a regular folder
    Returns: ('shared_drive', name) or ('folder', name) or (None, None) if not found
    """
    try:
        # First, try to get it as a regular file/folder
        file_info = drive_service.files().get(
            fileId=drive_id,
            fields="id, name, mimeType"
        ).execute()
        
        if file_info['mimeType'] == 'application/vnd.google-apps.folder':
            return ('folder', file_info['name'])
        else:
            return ('file', file_info['name'])
            
    except HttpError as e:
        if e.resp.status == 404:
            # If not found as regular file, try as shared drive
            try:
                drive_info = drive_service.drives().get(driveId=drive_id).execute()
                return ('shared_drive', drive_info['name'])
            except HttpError:
                return (None, None)
        else:
            return (None, None)

def download_files_in_folder(drive_service, folder_id, local_folder_path, is_shared_drive=False, shared_drive_id=None):
    """
    Download files from a folder, handling both shared drives and regular folders
    """
    query = f"'{folder_id}' in parents and trashed=false"
    
    if is_shared_drive:
        # Use shared drive parameters
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            corpora='drive',
            driveId=shared_drive_id or folder_id,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
    else:
        # Use regular folder parameters
        results = drive_service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()

    items = results.get('files', [])
    for item in items:
        file_id = item['id']
        file_name = item['name']
        mime_type = item['mimeType']
        if mime_type == 'application/vnd.google-apps.folder':
            new_folder_path = os.path.join(local_folder_path, sanitize_filename(file_name))
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)
            download_files_in_folder(drive_service, file_id, new_folder_path, is_shared_drive, shared_drive_id)
        else:
            download_file(drive_service, file_id, file_name, local_folder_path, mime_type)

def download_drive_files(drive_id):
    """
    Download all files from a drive (auto-detects if it's a shared drive or folder)
    """
    creds = get_service_account_credentials()
    drive_service = build('drive', 'v3', credentials=creds)
    
    # Detect the type of drive/folder
    drive_type, drive_name = detect_drive_type(drive_service, drive_id)
    
    if drive_type is None:
        print(f"❌ Could not access or find drive/folder with ID: {drive_id}")
        print("   Make sure:")
        print("   1. The ID is correct")
        print("   2. The service account has access to it")
        return False
    
    print(f"📁 Detected {drive_type}: '{drive_name}'")
    
    if drive_type == 'shared_drive':
        print("   Using shared drive API parameters...")
        download_files_in_folder(drive_service, drive_id, local_path, is_shared_drive=True, shared_drive_id=drive_id)
    elif drive_type == 'folder':
        print("   Using regular folder API parameters...")
        download_files_in_folder(drive_service, drive_id, local_path, is_shared_drive=False)
    else:
        print(f"❌ '{drive_name}' is a file, not a folder. Cannot download contents.")
        return False
    
    return True
    
def build_complete_file_tree(drive_service, root_id, is_shared_drive=False, shared_drive_id=None, current_path=""):
    """
    Build a complete hierarchical tree structure of all files and folders
    Returns a nested dictionary with full tree information
    """
    def get_files_in_folder(folder_id, folder_path=""):
        query = f"'{folder_id}' in parents and trashed=false"
        
        if is_shared_drive:
            results = drive_service.files().list(
                q=query,
                spaces='drive',
                corpora='drive',
                driveId=shared_drive_id or folder_id,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields="nextPageToken, files(id, name, mimeType, parents, size, modifiedTime, createdTime, webViewLink)",
                pageSize=1000  # Get more items per request
            ).execute()
        else:
            results = drive_service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, parents, size, modifiedTime, createdTime, webViewLink)",
                pageSize=1000
            ).execute()
        
        return results.get('files', [])
    
    def build_tree_recursive(folder_id, folder_name, current_path="", depth=0):
        """Recursively build tree structure"""
        if depth > 10:  # Prevent infinite recursion
            print(f"⚠️ Maximum depth reached for folder: {folder_name}")
            return None
        
        folder_path = f"{current_path}/{folder_name}" if current_path else folder_name
        print(f"{'  ' * depth}📁 Processing: {folder_path}")
        
        files = get_files_in_folder(folder_id, folder_path)
        
        tree_node = {
            "id": folder_id,
            "name": folder_name,
            "type": "folder",
            "path": folder_path,
            "depth": depth,
            "children": {
                "folders": {},
                "files": []
            },
            "metadata": {
                "total_files": 0,
                "total_folders": 0,
                "total_size": 0
            }
        }
        
        # Separate folders and files
        folders = [f for f in files if f['mimeType'] == 'application/vnd.google-apps.folder']
        regular_files = [f for f in files if f['mimeType'] != 'application/vnd.google-apps.folder']
        
        # Process files first
        for file_item in regular_files:
            file_size = int(file_item.get('size', 0)) if file_item.get('size') else 0
            file_info = {
                "id": file_item['id'],
                "name": file_item['name'],
                "type": "file",
                "mimeType": file_item['mimeType'],
                "path": f"{folder_path}/{file_item['name']}",
                "size": file_size,
                "size_human": format_file_size(file_size),
                "modifiedTime": file_item.get('modifiedTime'),
                "createdTime": file_item.get('createdTime'),
                "webViewLink": file_item.get('webViewLink'),
                "parents": file_item.get('parents', []),
                "depth": depth + 1
            }
            tree_node["children"]["files"].append(file_info)
            tree_node["metadata"]["total_files"] += 1
            tree_node["metadata"]["total_size"] += file_size
        
        # Process subfolders recursively
        for folder_item in folders:
            subfolder_tree = build_tree_recursive(
                folder_item['id'], 
                folder_item['name'], 
                folder_path, 
                depth + 1
            )
            if subfolder_tree:
                tree_node["children"]["folders"][folder_item['name']] = subfolder_tree
                # Aggregate metadata from subfolders
                tree_node["metadata"]["total_folders"] += 1 + subfolder_tree["metadata"]["total_folders"]
                tree_node["metadata"]["total_files"] += subfolder_tree["metadata"]["total_files"]
                tree_node["metadata"]["total_size"] += subfolder_tree["metadata"]["total_size"]
        
        return tree_node
    
    # Get root folder information
    try:
        if is_shared_drive:
            root_info = drive_service.drives().get(driveId=root_id).execute()
            root_name = root_info['name']
        else:
            root_info = drive_service.files().get(
                fileId=root_id,
                fields="id, name, mimeType"
            ).execute()
            root_name = root_info['name']
        
        print(f"🌳 Building complete file tree for: {root_name}")
        tree = build_tree_recursive(root_id, root_name)
        
        if tree:
            print(f"\n📊 Tree Summary:")
            print(f"   Total Folders: {tree['metadata']['total_folders']}")
            print(f"   Total Files: {tree['metadata']['total_files']}")
            print(f"   Total Size: {tree['metadata']['total_size']:,} bytes ({format_file_size(tree['metadata']['total_size'])})")
        
        return tree
        
    except Exception as e:
        print(f"❌ Error building tree: {e}")
        return None

def format_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def print_tree_structure(tree, show_files=True, max_depth=None, show_size=True):
    """
    Print a visual tree structure in the console
    """
    if not tree:
        print("❌ No tree to display")
        return
    
    def print_node(node, prefix="", is_last=True, current_depth=0):
        if max_depth is not None and current_depth > max_depth:
            return
        
        # Choose the appropriate connector
        connector = "└── " if is_last else "├── "
        
        # Node icon and name
        if node['type'] == 'folder':
            icon = "📁"
            name = node['name']
            if show_size and 'metadata' in node:
                size_info = f" ({node['metadata']['total_files']} files, {format_file_size(node['metadata']['total_size'])})"
                name += size_info
        else:
            icon = "📄"
            name = node['name']
            if show_size and 'size' in node:
                name += f" ({format_file_size(node['size'])})"
        
        print(f"{prefix}{connector}{icon} {name}")
        
        # Prepare prefix for children
        child_prefix = prefix + ("    " if is_last else "│   ")
        
        if node['type'] == 'folder' and 'children' in node:
            # Get all children (folders and files)
            children = []
            
            # Add folders first
            if 'folders' in node['children']:
                for folder_name, folder_node in node['children']['folders'].items():
                    children.append(folder_node)
            
            # Add files if requested
            if show_files and 'files' in node['children']:
                children.extend(node['children']['files'])
            
            # Print children
            for i, child in enumerate(children):
                is_last_child = (i == len(children) - 1)
                print_node(child, child_prefix, is_last_child, current_depth + 1)
    
    print(f"\n🌳 Tree Structure: {tree['name']}")
    print("=" * 50)
    print_node(tree)
    print("=" * 50)

def generate_mermaid_graph(tree, include_files=True, max_depth=5):
    """
    Generate a Mermaid graph representation of the tree structure
    """
    if not tree:
        return None
    
    mermaid_lines = ["graph TD"]
    node_id_counter = 0
    node_mapping = {}
    
    def get_node_id(node_info):
        nonlocal node_id_counter
        node_key = f"{node_info['id']}_{node_info['name']}"
        if node_key not in node_mapping:
            node_mapping[node_key] = f"node{node_id_counter}"
            node_id_counter += 1
        return node_mapping[node_key]
    
    def sanitize_label(text):
        """Sanitize text for Mermaid diagram"""
        return text.replace('"', '\\"').replace('\n', ' ').replace('\r', '')
    
    def add_node_to_graph(node, parent_id=None, current_depth=0):
        if max_depth is not None and current_depth > max_depth:
            return
        
        node_id = get_node_id(node)
        
        # Create node label
        if node['type'] == 'folder':
            label = f"📁 {sanitize_label(node['name'])}"
            style_class = "folder"
        else:
            label = f"📄 {sanitize_label(node['name'])}"
            style_class = "file"
        
        # Add node definition
        mermaid_lines.append(f'    {node_id}["{label}"]')
        
        # Add edge from parent
        if parent_id:
            mermaid_lines.append(f"    {parent_id} --> {node_id}")
        
        # Add styling
        mermaid_lines.append(f"    {node_id}:::{style_class}")
        
        # Process children for folders
        if node['type'] == 'folder' and 'children' in node:
            # Add subfolders
            if 'folders' in node['children']:
                for folder_node in node['children']['folders'].values():
                    add_node_to_graph(folder_node, node_id, current_depth + 1)
            
            # Add files if requested
            if include_files and 'files' in node['children']:
                for file_node in node['children']['files']:
                    add_node_to_graph(file_node, node_id, current_depth + 1)
    
    # Start with root node
    add_node_to_graph(tree)
    
    # Add CSS styling
    mermaid_lines.extend([
        "",
        "    classDef folder fill:#e1f5fe,stroke:#01579b,stroke-width:2px,color:#000",
        "    classDef file fill:#f3e5f5,stroke:#4a148c,stroke-width:1px,color:#000"
    ])
    
    return "\n".join(mermaid_lines)

def save_graph_visualizations(tree, drive_id, output_dir):
    """
    Save different graph visualization formats
    """
    if not tree:
        return
    
    base_filename = f"drive_graph_{drive_id}_{tree['name'].replace(' ', '_').replace('/', '_')}"
    
    # Save Mermaid graph (folders only)
    mermaid_folders = generate_mermaid_graph(tree, include_files=False, max_depth=5)
    if mermaid_folders:
        mermaid_file = os.path.join(output_dir, f"{base_filename}_folders.mmd")
        with open(mermaid_file, 'w', encoding='utf-8') as f:
            f.write(mermaid_folders)
        print(f"📊 Mermaid graph (folders) saved to: {mermaid_file}")
    
    # Save Mermaid graph (with files, limited depth)
    mermaid_full = generate_mermaid_graph(tree, include_files=True, max_depth=3)
    if mermaid_full:
        mermaid_file_full = os.path.join(output_dir, f"{base_filename}_full.mmd")
        with open(mermaid_file_full, 'w', encoding='utf-8') as f:
            f.write(mermaid_full)
        print(f"📊 Mermaid graph (with files) saved to: {mermaid_file_full}")
    
    # Save text tree representation
    import io
    import sys
    
    # Capture print output
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    
    try:
        print_tree_structure(tree, show_files=True, max_depth=4, show_size=True)
        tree_text = buffer.getvalue()
    finally:
        sys.stdout = old_stdout
    
    tree_file = os.path.join(output_dir, f"{base_filename}_text.txt")
    with open(tree_file, 'w', encoding='utf-8') as f:
        f.write(tree_text)
    print(f"📋 Text tree saved to: {tree_file}")

def display_tree_visualization(tree):
    """
    Display tree visualization in console with options
    """
    if not tree:
        print("❌ No tree to visualize")
        return
    
    while True:
        print(f"\n🎨 Tree Visualization Options for: {tree['name']}")
        print("=" * 50)
        print("1. Show tree structure (folders only)")
        print("2. Show tree structure (with files)")
        print("3. Show tree structure (limited depth)")
        print("4. Show summary statistics")
        print("5. Generate and save Mermaid graphs")
        print("6. Back to main menu")
        
        choice = input("Enter your choice (1-6): ").strip()
        
        if choice == "1":
            print_tree_structure(tree, show_files=False, show_size=True)
        elif choice == "2":
            print_tree_structure(tree, show_files=True, show_size=True)
        elif choice == "3":
            try:
                depth = int(input("Enter maximum depth to show (1-10): "))
                if 1 <= depth <= 10:
                    print_tree_structure(tree, show_files=True, max_depth=depth, show_size=True)
                else:
                    print("❌ Please enter a depth between 1 and 10")
            except ValueError:
                print("❌ Please enter a valid number")
        elif choice == "4":
            print(f"\n📊 Tree Statistics for: {tree['name']}")
            print("=" * 40)
            print(f"Total Folders: {tree['metadata']['total_folders']:,}")
            print(f"Total Files: {tree['metadata']['total_files']:,}")
            print(f"Total Size: {format_file_size(tree['metadata']['total_size'])}")
            print(f"Tree Depth: {tree['depth']}")
            
            # Show folder breakdown
            if 'children' in tree and 'folders' in tree['children']:
                print(f"\nTop-level folders ({len(tree['children']['folders'])}):")
                for folder_name, folder_info in tree['children']['folders'].items():
                    print(f"  📁 {folder_name}: {folder_info['metadata']['total_files']} files, {format_file_size(folder_info['metadata']['total_size'])}")
        elif choice == "5":
            output_dir = os.path.join(os.getcwd(), "drive_structure")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            save_graph_visualizations(tree, tree['id'], output_dir)
            print("\n💡 Tip: You can view Mermaid graphs at https://mermaid.live/")
        elif choice == "6":
            break
        else:
            print("❌ Invalid choice. Please select 1-6.")

def flatten_tree_to_paths(tree, include_folders=True):
    """
    Flatten the tree structure to a list of all paths
    Useful for LLM to understand all available paths
    """
    paths = []
    
    def extract_paths(node, current_path=""):
        if include_folders and node['type'] == 'folder':
            paths.append({
                "path": node['path'],
                "type": "folder",
                "id": node['id'],
                "name": node['name'],
                "total_files": node['metadata']['total_files'],
                "total_folders": node['metadata']['total_folders']
            })
        
        # Add all files in this folder
        for file_info in node.get('children', {}).get('files', []):
            paths.append({
                "path": file_info['path'],
                "type": "file",
                "id": file_info['id'],
                "name": file_info['name'],
                "mimeType": file_info['mimeType'],
                "size": file_info['size'],
                "size_human": file_info['size_human']
            })
        
        # Recursively process subfolders
        for subfolder in node.get('children', {}).get('folders', {}).values():
            extract_paths(subfolder, current_path)
    
    if tree:
        extract_paths(tree)
    
    return sorted(paths, key=lambda x: x['path'])

def save_tree_structure(tree, drive_id, output_format='both'):
    """
    Save the tree structure to files in different formats
    """
    if not tree:
        print("❌ No tree to save")
        return
    
    timestamp = json.loads(json.dumps(tree['metadata'], default=str))
    
    # Create output directory
    output_dir = os.path.join(os.getcwd(), "drive_structure")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    base_filename = f"drive_structure_{drive_id}_{json.loads(json.dumps(tree['name'], default=str)).replace(' ', '_').replace('/', '_')}"
    
    if output_format in ['json', 'both']:
        # Save complete tree structure
        tree_file = os.path.join(output_dir, f"{base_filename}_complete.json")
        with open(tree_file, 'w', encoding='utf-8') as f:
            json.dump(tree, f, indent=2, ensure_ascii=False, default=str)
        print(f"💾 Complete tree saved to: {tree_file}")
    
    if output_format in ['paths', 'both']:
        # Save flattened paths for easy LLM consumption
        paths = flatten_tree_to_paths(tree)
        paths_file = os.path.join(output_dir, f"{base_filename}_paths.json")
        with open(paths_file, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {
                    "drive_id": drive_id,
                    "drive_name": tree['name'],
                    "total_paths": len(paths),
                    "total_files": tree['metadata']['total_files'],
                    "total_folders": tree['metadata']['total_folders'],
                    "total_size": tree['metadata']['total_size'],
                    "total_size_human": format_file_size(tree['metadata']['total_size']),
                    "generated_at": json.dumps(json.loads(json.dumps({}, default=str)), default=str)
                },
                "paths": paths
            }, f, indent=2, ensure_ascii=False, default=str)
        print(f"💾 Flattened paths saved to: {paths_file}")
    
    # Always save graph visualizations
    save_graph_visualizations(tree, drive_id, output_dir)
    
    return output_dir

def get_complete_file_tree(drive_id, save_to_file=True, output_format='both'):
    """
    Get complete hierarchical tree structure of all files and folders
    """
    creds = get_service_account_credentials()
    drive_service = build('drive', 'v3', credentials=creds)
    
    # Detect the type of drive/folder
    drive_type, drive_name = detect_drive_type(drive_service, drive_id)
    
    if drive_type is None:
        print(f"❌ Could not access or find drive/folder with ID: {drive_id}")
        return None
    
    print(f"📁 Detected {drive_type}: '{drive_name}'")
    
    # Build complete tree
    if drive_type == 'shared_drive':
        tree = build_complete_file_tree(drive_service, drive_id, is_shared_drive=True, shared_drive_id=drive_id)
    elif drive_type == 'folder':
        tree = build_complete_file_tree(drive_service, drive_id, is_shared_drive=False)
    else:
        print(f"❌ '{drive_name}' is a file, not a folder. Cannot build tree.")
        return None
    
    if tree and save_to_file:
        save_tree_structure(tree, drive_id, output_format)
    
    return tree

def get_all_file_routes_in_JSON(drive_id):
    """
    Get all file information from a drive/folder in JSON format (legacy function - now uses tree structure)
    """
    tree = get_complete_file_tree(drive_id, save_to_file=False)
    
    if not tree:
        return []
    
    # Convert tree to flat list for backward compatibility
    def flatten_to_list(node):
        items = []
        
        # Add current folder info
        if node['type'] == 'folder':
            items.append({
                'id': node['id'],
                'name': node['name'],
                'mimeType': 'application/vnd.google-apps.folder',
                'path': node['path'],
                'depth': node['depth']
            })
        
        # Add all files in this folder
        for file_info in node.get('children', {}).get('files', []):
            items.append({
                'id': file_info['id'],
                'name': file_info['name'],
                'mimeType': file_info['mimeType'],
                'path': file_info['path'],
                'depth': file_info['depth'],
                'size': file_info['size'],
                'parents': file_info['parents']
            })
        
        # Recursively add subfolders
        for subfolder in node.get('children', {}).get('folders', {}).values():
            items.extend(flatten_to_list(subfolder))
        
        return items
    
    return flatten_to_list(tree)

# Legacy functions for backward compatibility
def download_shared_drive_files(shared_drive_id):
    """
    Download all files from a shared drive (legacy function)
    """
    return download_drive_files(shared_drive_id)

if __name__ == "__main__":
    # Print service account email for reference
    try:
        service_email = get_service_account_email()
        print(f"Service Account Email: {service_email}")
        print(f"Make sure this email has been granted access to the drive/folder!")
        print("-" * 60)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please create a service_account.json file with your service account credentials.")
        print("Instructions:")
        print("1. Go to Google Cloud Console")
        print("2. Create a new service account or use existing one")
        print("3. Download the JSON key file")
        print("4. Rename it to 'service_account.json' and place it in this directory")
        print("5. Grant the service account access to your drive/folder")
        exit(1)
    
    print("\n📚 DRIVE TYPES SUPPORTED:")
    print("✅ Shared Drives (Team Drives)")
    print("✅ Shared Folders (Regular folders shared with you)")
    print("✅ Auto-detection of drive type")
    print("-" * 60)
    
    drive_id = input("Enter your Drive/Folder ID: ")
    
    # Ask user what they want to do
    print("\nSelect an option:")
    print("1. Download all files from drive/folder")
    print("2. Get file information in JSON format (flat list)")
    print("3. Build complete hierarchical tree structure")
    print("4. Build tree structure and download files")
    print("5. Load existing tree and visualize")
    choice = input("Enter your choice (1-5): ").strip()
    
    if choice == "1":
        print(f"Downloading files to: {local_path}")
        success = download_drive_files(drive_id)
        if success:
            print("✅ Download completed!")
        else:
            print("❌ Download failed!")
            
    elif choice == "2":
        print("Getting file information...")
        files_info = get_all_file_routes_in_JSON(drive_id)
        if files_info:
            print(json.dumps(files_info, indent=2, ensure_ascii=False))
        else:
            print("❌ No files found or access denied!")
            
    elif choice == "3":
        print("Building complete hierarchical tree structure...")
        tree = get_complete_file_tree(drive_id, save_to_file=True, output_format='both')
        if tree:
            print("✅ Tree structure generated and saved!")
            print(f"📊 Summary:")
            print(f"   Root: {tree['name']}")
            print(f"   Total Folders: {tree['metadata']['total_folders']}")
            print(f"   Total Files: {tree['metadata']['total_files']}")
            print(f"   Total Size: {format_file_size(tree['metadata']['total_size'])}")
            
            # Show first few paths as example
            paths = flatten_tree_to_paths(tree)
            print(f"\n📁 Sample paths (showing first 10):")
            for path_info in paths[:10]:
                icon = "📁" if path_info['type'] == 'folder' else "📄"
                print(f"   {icon} {path_info['path']}")
            if len(paths) > 10:
                print(f"   ... and {len(paths) - 10} more paths")
            
            # Offer visualization
            visualize = input("\nWould you like to visualize the tree structure? (y/n): ").lower().strip()
            if visualize == 'y':
                display_tree_visualization(tree)
        else:
            print("❌ Failed to build tree structure!")
            
    elif choice == "4":
        print("Building tree structure and downloading files...")
        tree = get_complete_file_tree(drive_id, save_to_file=True, output_format='both')
        if tree:
            print("✅ Tree structure generated!")
            print(f"Downloading files to: {local_path}")
            success = download_drive_files(drive_id)
            if success:
                print("✅ Download completed!")
                
                # Offer visualization
                visualize = input("\nWould you like to visualize the tree structure? (y/n): ").lower().strip()
                if visualize == 'y':
                    display_tree_visualization(tree)
            else:
                print("❌ Download failed!")
        else:
            print("❌ Failed to build tree structure!")
            
    elif choice == "5":
        print("Loading existing tree structure...")
        structure_dir = os.path.join(os.getcwd(), "drive_structure")
        if not os.path.exists(structure_dir):
            print("❌ No drive_structure directory found. Please build a tree first (option 3 or 4).")
        else:
            # List available tree files
            tree_files = [f for f in os.listdir(structure_dir) if f.endswith('_complete.json')]
            if not tree_files:
                print("❌ No tree structure files found. Please build a tree first (option 3 or 4).")
            else:
                print(f"\nAvailable tree structures:")
                for i, filename in enumerate(tree_files, 1):
                    print(f"{i}. {filename}")
                
                try:
                    file_choice = int(input(f"Select file (1-{len(tree_files)}): ")) - 1
                    if 0 <= file_choice < len(tree_files):
                        tree_file = os.path.join(structure_dir, tree_files[file_choice])
                        with open(tree_file, 'r', encoding='utf-8') as f:
                            tree = json.load(f)
                        print(f"✅ Loaded tree structure: {tree['name']}")
                        display_tree_visualization(tree)
                    else:
                        print("❌ Invalid selection")
                except (ValueError, json.JSONDecodeError) as e:
                    print(f"❌ Error loading tree: {e}")
    else:
        print("Invalid choice. Please run the script again and select 1-5.")