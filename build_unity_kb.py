#!/usr/bin/env python3
"""
Unity Knowledge Base Builder for Qdrant
Based on research: Architectural Strategy for Unity Documentation RAG Systems
"""

import os
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

def parse_meta_file(meta_path: Path) -> Optional[str]:
    """Extract GUID from Unity .meta file"""
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('guid:'):
                    return line.split(':')[1].strip()
    except Exception as e:
        print(f"Error parsing meta file {meta_path}: {e}")
    return None

def find_assembly_definition(file_path: Path, project_root: Path) -> Optional[str]:
    """Walk up directory tree to find nearest .asmdef file"""
    current = file_path.parent
    while current >= project_root:
        asmdef_files = list(current.glob('*.asmdef'))
        if asmdef_files:
            try:
                with open(asmdef_files[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('name', 'UnknownAssembly')
            except:
                pass
        if current == project_root:
            break
        current = current.parent
    return 'Assembly-CSharp'  # Default Unity assembly

def determine_code_type(file_path: Path) -> str:
    """Determine if code is editor, runtime, or test"""
    path_str = str(file_path).lower()
    if '/editor/' in path_str or '\\editor\\' in path_str:
        return 'editor'
    elif '/tests/' in path_str or '\\tests\\' in path_str:
        return 'test'
    else:
        return 'runtime'

def extract_class_name(content: str) -> Optional[str]:
    """Simple regex to extract primary class name from C# file"""
    import re
    # Look for class declarations
    match = re.search(r'class\s+(\w+)', content)
    if match:
        return match.group(1)
    return None

def generate_deterministic_uuid(asset_guid: str, chunk_index: int) -> str:
    """Generate UUID v5 based on asset GUID and chunk index"""
    namespace = uuid.NAMESPACE_DNS
    seed = f"{asset_guid}_{chunk_index}"
    return str(uuid.uuid5(namespace, seed))

def scan_unity_project(project_path: str) -> List[Dict]:
    """
    Scan Unity project and prepare metadata for Qdrant ingestion
    Returns list of documents ready for embedding and indexing
    """
    project_root = Path(project_path)
    documents = []
    
    # Directories to scan
    scan_dirs = ['Assets', 'Packages']
    
    # Directories to exclude
    exclude_dirs = {'Library', 'Temp', 'Logs', 'Build', 'Builds'}
    
    print(f"Scanning project: {project_root}")
    print("=" * 60)
    
    for scan_dir in scan_dirs:
        scan_path = project_root / scan_dir
        if not scan_path.exists():
            continue
            
        print(f"\n📁 Scanning {scan_dir}/...")
        
        # Find all .cs files
        for cs_file in scan_path.rglob('*.cs'):
            # Skip if in excluded directory
            if any(excluded in cs_file.parts for excluded in exclude_dirs):
                continue
                
            # Find companion .meta file
            meta_file = cs_file.with_suffix('.cs.meta')
            if not meta_file.exists():
                print(f"  ⚠️  Missing .meta for {cs_file.name}")
                continue
                
            # Extract metadata
            asset_guid = parse_meta_file(meta_file)
            if not asset_guid:
                print(f"  ⚠️  No GUID found for {cs_file.name}")
                continue
                
            assembly_name = find_assembly_definition(cs_file, project_root)
            code_type = determine_code_type(cs_file)
            
            # Read content
            try:
                with open(cs_file, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"  ⚠️  Error reading {cs_file.name}: {e}")
                continue
                
            class_name = extract_class_name(content)
            file_path = str(cs_file.relative_to(project_root))
            
            # Create document metadata
            doc = {
                'asset_guid': asset_guid,
                'file_path': file_path,
                'assembly_name': assembly_name,
                'code_type': code_type,
                'class_name': class_name or 'Unknown',
                'content': content,
                'content_hash': hashlib.sha256(content.encode()).hexdigest()[:12]
            }
            
            documents.append(doc)
            print(f"  ✅ {file_path}")
            print(f"      GUID: {asset_guid}")
            print(f"      Assembly: {assembly_name}")
            print(f"      Type: {code_type}")
            if class_name:
                print(f"      Class: {class_name}")
    
    return documents

def main():
    # Configuration
    PROJECT_PATH = "/a0/usr/projects/unitymlcreator"
    
    print("\n" + "=" * 60)
    print("🎮 UNITY KNOWLEDGE BASE BUILDER")
    print("=" * 60)
    
    # Scan project
    documents = scan_unity_project(PROJECT_PATH)
    
    print("\n" + "=" * 60)
    print(f"📊 SCAN COMPLETE")
    print("=" * 60)
    print(f"Total files found: {len(documents)}")
    
    # Group by code type
    by_type = {}
    for doc in documents:
        code_type = doc['code_type']
        by_type[code_type] = by_type.get(code_type, 0) + 1
    
    print("\nBreakdown by type:")
    for code_type, count in sorted(by_type.items()):
        print(f"  {code_type}: {count}")
    
    # Save metadata to JSON for review
    output_file = "/tmp/unity_kb_metadata.json"
    with open(output_file, 'w') as f:
        json.dump(documents, f, indent=2)
    
    print(f"\n✅ Metadata saved to: {output_file}")
    print("\nNext steps:")
    print("1. Review the metadata file")
    print("2. Create Qdrant collection with hybrid search")
    print("3. Generate embeddings using Voyage-Code-2")
    print("4. Upsert to Qdrant with proper payload schema")
    
    return documents

if __name__ == "__main__":
    main()
