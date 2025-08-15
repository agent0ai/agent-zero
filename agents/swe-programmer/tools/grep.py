"""
Grep Tool for SWE Programmer Agent
Advanced code searching functionality
"""

import os
import re
import fnmatch
from pathlib import Path
from typing import List, Tuple
from python.helpers.tool import Tool, Response

class Grep(Tool):
    """
    Tool for searching code patterns in files
    """
    
    async def execute(self, **kwargs):
        """Execute grep search operations"""
        
        pattern = kwargs.get("pattern")
        if not pattern:
            return Response(
                message="Error: 'pattern' parameter is required for grep",
                break_loop=False
            )
        
        # Get search parameters
        path = kwargs.get("path", ".")
        file_pattern = kwargs.get("file_pattern", "*")
        recursive = kwargs.get("recursive", True)
        case_sensitive = kwargs.get("case_sensitive", True)
        regex = kwargs.get("regex", False)
        context_lines = kwargs.get("context_lines", 0)
        max_results = kwargs.get("max_results", 100)
        
        # Perform search
        results = await self.search_files(
            pattern=pattern,
            path=path,
            file_pattern=file_pattern,
            recursive=recursive,
            case_sensitive=case_sensitive,
            regex=regex,
            context_lines=context_lines,
            max_results=max_results
        )
        
        if not results:
            return Response(
                message=f"No matches found for pattern: {pattern}",
                break_loop=False
            )
        
        # Format results
        formatted = self.format_results(results, pattern, context_lines)
        
        return Response(message=formatted, break_loop=False)
    
    async def search_files(self, pattern: str, path: str, file_pattern: str,
                          recursive: bool, case_sensitive: bool, regex: bool,
                          context_lines: int, max_results: int) -> List[Tuple]:
        """Search for pattern in files"""
        results = []
        count = 0
        
        # Compile pattern
        if regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                compiled_pattern = re.compile(pattern, flags)
            except re.error as e:
                return []  # Invalid regex
        else:
            if not case_sensitive:
                pattern = pattern.lower()
        
        # Get files to search
        files_to_search = self.get_files_to_search(path, file_pattern, recursive)
        
        for file_path in files_to_search:
            if count >= max_results:
                break
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    if count >= max_results:
                        break
                    
                    # Check for match
                    matched = False
                    if regex:
                        if compiled_pattern.search(line):
                            matched = True
                    else:
                        search_line = line if case_sensitive else line.lower()
                        if pattern in search_line:
                            matched = True
                    
                    if matched:
                        # Get context lines if requested
                        context_before = []
                        context_after = []
                        
                        if context_lines > 0:
                            start = max(0, line_num - context_lines - 1)
                            end = min(len(lines), line_num + context_lines)
                            
                            context_before = [
                                (i+1, lines[i].rstrip()) 
                                for i in range(start, line_num-1)
                            ]
                            context_after = [
                                (i+1, lines[i].rstrip()) 
                                for i in range(line_num, end)
                            ]
                        
                        results.append((
                            file_path,
                            line_num,
                            line.rstrip(),
                            context_before,
                            context_after
                        ))
                        count += 1
                        
            except Exception:
                continue  # Skip files that can't be read
        
        return results
    
    def get_files_to_search(self, path: str, file_pattern: str, recursive: bool) -> List[str]:
        """Get list of files to search based on patterns"""
        files = []
        
        if os.path.isfile(path):
            # Single file specified
            return [path]
        
        if not os.path.isdir(path):
            return []
        
        # Directory search
        if recursive:
            for root, dirs, filenames in os.walk(path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for filename in filenames:
                    if fnmatch.fnmatch(filename, file_pattern):
                        files.append(os.path.join(root, filename))
        else:
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                if os.path.isfile(file_path) and fnmatch.fnmatch(filename, file_pattern):
                    files.append(file_path)
        
        return files
    
    def format_results(self, results: List[Tuple], pattern: str, context_lines: int) -> str:
        """Format search results for display"""
        if not results:
            return "No matches found."
        
        output = [f"Found {len(results)} match(es) for pattern: {pattern}\n"]
        
        # Group results by file
        by_file = {}
        for file_path, line_num, line, before, after in results:
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append((line_num, line, before, after))
        
        for file_path, matches in by_file.items():
            output.append(f"\n{file_path}:")
            
            for line_num, line, before, after in matches:
                if context_lines > 0 and before:
                    for ctx_num, ctx_line in before:
                        output.append(f"  {ctx_num:4d}: {ctx_line}")
                
                # Highlight the matching line
                output.append(f"→ {line_num:4d}: {line}")
                
                if context_lines > 0 and after:
                    for ctx_num, ctx_line in after:
                        output.append(f"  {ctx_num:4d}: {ctx_line}")
                
                if context_lines > 0:
                    output.append("")  # Blank line between matches
        
        return "\n".join(output)