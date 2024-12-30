#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def read_file_contents(file_path):
    """Read and return file contents, with basic error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def save_important_files(root_dir, output_file):
    """
    Extract and save contents of important files from the browser extension project.
    Focuses on source code, configuration, and manifest files while excluding build artifacts.
    """
    # Define important file patterns
    important_patterns = {
        # Source files
        '.ts': 'TypeScript Source',
        '.tsx': 'React TypeScript Component',
        '.scss': 'Styles',
        # Configuration
        'manifest.json': 'Extension Manifest',
        'package.json': 'Project Configuration',
        'tsconfig.json': 'TypeScript Configuration',
        'webpack.config.js': 'Webpack Configuration',
        # Other important files
        '.d.ts': 'TypeScript Declarations',
    }
    
    # Define directories to skip
    skip_dirs = {'node_modules', 'build', '__pycache__'}
    
    with open(output_file, 'w', encoding='utf-8') as out:
        out.write("# Browser Extension Project Contents\n\n")
        
        for root, dirs, files in os.walk(root_dir):
            # Skip unnecessary directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            # Process each file
            for file in sorted(files):
                file_path = Path(root) / file
                
                # Check if file is important based on extension or exact name
                is_important = any(
                    pattern in file_path.name if pattern.startswith('.') 
                    else pattern == file_path.name 
                    for pattern in important_patterns
                )
                
                if is_important:
                    # Get relative path from project root
                    rel_path = file_path.relative_to(root_dir)
                    
                    # Determine file type
                    file_type = next(
                        desc for pattern, desc in important_patterns.items()
                        if pattern in file_path.name
                    )
                    
                    # Write file header
                    out.write(f"\n{'='*80}\n")
                    out.write(f"File: {rel_path}\n")
                    out.write(f"Type: {file_type}\n")
                    out.write('='*80 + '\n\n')
                    
                    # Write file contents
                    contents = read_file_contents(file_path)
                    out.write(contents)
                    out.write('\n')

if __name__ == "__main__":
    # Get project root directory from command line or use current directory
    root_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    output_file = "extension_contents.txt"
    
    save_important_files(root_dir, output_file)
    print(f"Important files have been saved to {output_file}")
