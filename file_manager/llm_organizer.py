"""
LLM Organizer - Use LLM to suggest intelligent folder structure
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


def prepare_files_for_llm(folder_path: Path) -> Dict:
    """
    Prepare file list for LLM analysis
    
    Args:
        folder_path: Path to the folder
    
    Returns:
        Dictionary with file information
    """
    if not folder_path.exists():
        return {"error": f"Folder does not exist: {folder_path}"}
    
    files = []
    extensions = set()
    
    try:
        for file_path in folder_path.iterdir():
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "extension": file_path.suffix.lower(),
                    "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                })
                extensions.add(file_path.suffix.lower())
    
    except Exception as e:
        return {"error": str(e)}
    
    return {
        "total_files": len(files),
        "files": files,
        "extensions_found": sorted(list(extensions)),
    }


def generate_llm_prompt(folder_info: Dict) -> str:
    """
    Generate a prompt to send to LLM for organizing files
    
    Args:
        folder_info: Dictionary with file information
    
    Returns:
        Prompt string
    """
    files_list = "\n".join([f"- {f['name']}" for f in folder_info.get("files", [])[:50]])
    
    prompt = f"""You are a file organization expert. I have a folder with {folder_info['total_files']} files.

Here are the file names:
{files_list}

Please suggest an optimal folder structure to organize these files. Consider:
1. File types and extensions
2. Related files that should be grouped together
3. Project structure if applicable
4. Logical categorization

Return a JSON object with this structure:
{{
    "suggested_structure": {{
        "folder_name_1": ["file1.ext", "file2.ext"],
        "folder_name_2": ["file3.ext", "file4.ext"],
        "root_level": ["file_to_keep_at_root.ext"]
    }},
    "reasoning": "Explain your organization logic",
    "notes": "Any additional suggestions"
}}

IMPORTANT: Return ONLY valid JSON, no other text."""
    
    return prompt


def parse_llm_response(response: str) -> Optional[Dict]:
    """
    Parse LLM response to extract folder structure
    
    Args:
        response: Response from LLM
    
    Returns:
        Parsed structure or None if parsing fails
    """
    try:
        # Try to extract JSON from response
        start = response.find("{")
        end = response.rfind("}") + 1
        
        if start >= 0 and end > start:
            json_str = response[start:end]
            data = json.loads(json_str)
            return data
    except json.JSONDecodeError:
        pass
    
    return None


def apply_llm_organization(folder_path: Path, organization_plan: Dict, dry_run: bool = False) -> Dict:
    """
    Apply the LLM-suggested organization to actual files
    
    Args:
        folder_path: Path to the folder
        organization_plan: Dictionary with folder structure from LLM
        dry_run: If True, don't actually move files
    
    Returns:
        Dictionary with application results
    """
    if not folder_path.exists():
        return {"error": f"Folder does not exist: {folder_path}"}
    
    results = {
        "folders_created": 0,
        "files_moved": 0,
        "files_unchanged": 0,
        "errors": [],
        "organization_map": {},
    }
    
    try:
        structure = organization_plan.get("suggested_structure", {})
        
        # Create a mapping of filename to target folder
        file_to_folder = {}
        for folder_name, files in structure.items():
            if folder_name != "root_level":
                for filename in files:
                    file_to_folder[filename] = folder_name
        
        # Process files
        for file_path in folder_path.iterdir():
            if file_path.is_file():
                filename = file_path.name
                
                if filename in file_to_folder:
                    target_folder = folder_path / file_to_folder[filename]
                    
                    if not dry_run:
                        target_folder.mkdir(exist_ok=True)
                        import shutil
                        
                        destination = target_folder / filename
                        if destination.exists():
                            import os
                            name, ext = os.path.splitext(filename)
                            from datetime import datetime
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            destination = target_folder / f"{name}_{timestamp}{ext}"
                        
                        shutil.move(str(file_path), str(destination))
                        results["files_moved"] += 1
                    
                    if file_to_folder[filename] not in results["organization_map"]:
                        results["organization_map"][file_to_folder[filename]] = []
                    
                    results["organization_map"][file_to_folder[filename]].append(filename)
                else:
                    results["files_unchanged"] += 1
    
    except Exception as e:
        results["error"] = str(e)
    
    return results
