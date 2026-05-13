"""JSON handling utilities for IBM Cloud collector."""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


def normalize_resource(
    resource_id: str,
    resource_type: str,
    provider: str,
    region: str,
    configuration: Dict[str, Any],
    tags: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Normalize resource data into consistent JSON schema.
    
    Args:
        resource_id: Unique identifier for the resource
        resource_type: Type of resource (e.g., 'virtual_server', 'vpc', 'security_group')
        provider: Cloud provider (always 'ibm_cloud')
        region: IBM Cloud region
        configuration: Resource-specific configuration details
        tags: Optional resource tags
        metadata: Optional additional metadata
        
    Returns:
        Normalized resource dictionary
    """
    normalized = {
        "resource_id": resource_id,
        "resource_type": resource_type,
        "provider": provider,
        "region": region,
        "configuration": configuration,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if tags:
        normalized["tags"] = tags
    
    if metadata:
        normalized["metadata"] = metadata
    
    return normalized


def save_json(
    data: Any,
    filename: str,
    output_dir: str = 'output',
    use_timestamp: bool = True
) -> str:
    """
    Save data to JSON file with optional timestamp.
    
    Args:
        data: Data to save (dict, list, or any JSON-serializable object)
        filename: Base filename (without extension)
        output_dir: Output directory path
        use_timestamp: Whether to add timestamp to filename
        
    Returns:
        Path to saved file
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate filename with optional timestamp
    if use_timestamp:
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        full_filename = f"{filename}_{timestamp}.json"
    else:
        full_filename = f"{filename}.json"
    
    filepath = os.path.join(output_dir, full_filename)
    
    # Save to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return filepath


def load_json(filepath: str) -> Any:
    """
    Load data from JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded data
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def merge_json_files(
    input_files: list,
    output_file: str,
    output_dir: str = 'output'
) -> str:
    """
    Merge multiple JSON files into one.
    
    Args:
        input_files: List of input file paths
        output_file: Output filename
        output_dir: Output directory
        
    Returns:
        Path to merged file
    """
    merged_data = []
    
    for filepath in input_files:
        if os.path.exists(filepath):
            data = load_json(filepath)
            if isinstance(data, list):
                merged_data.extend(data)
            else:
                merged_data.append(data)
    
    return save_json(merged_data, output_file, output_dir, use_timestamp=True)


