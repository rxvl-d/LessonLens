#!/usr/bin/env python3
import os
from pathlib import Path

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def save_contents(root_dir, output_file):
    important_patterns = {
        '.py': 'Python Source',
        'requirements.txt': 'Dependencies',
        'Makefile': 'Build Configuration',
        'Procfile': 'Deployment Configuration',
        'runtime.txt': 'Python Runtime',
        '.ipynb': 'Jupyter Notebook'
    }
    
    skip_dirs = {'__pycache__', 'data', 'models', '.git'}
    
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write("# Backend Project Contents\n\n")
        
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in sorted(files):
                file_path = Path(root) / file
                
                if any(pattern in file_path.name for pattern in important_patterns):
                    rel_path = file_path.relative_to(root_dir)
                    file_type = next(
                        desc for pattern, desc in important_patterns.items()
                        if pattern in file_path.name
                    )
                    
                    out.write(f"\n{'='*80}\n")
                    out.write(f"File: {rel_path}\n")
                    out.write(f"Type: {file_type}\n")
                    out.write('='*80 + '\n\n')
                    out.write(read_file(file_path))
                    out.write('\n')

if __name__ == "__main__":
    save_contents('.', 'backend_contents.txt')
    print("Contents saved to backend_contents.txt")
