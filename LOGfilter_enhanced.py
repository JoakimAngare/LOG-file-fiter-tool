import os
import re
import argparse
import json
import zipfile
import tempfile
import shutil
from pathlib import Path

# Color code key words
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

def filter_log_file(file_path, keyword_patterns, highlight_words=None):
    """
    Filter lines from a LOG file that contain any of the specified keywords.
    
    Args:
        file_path (str): Path to the input LOG file
        keyword_patterns (list): List of compiled regex patterns to search for
        highlight_words (dict, optional): Dictionary mapping words to highlight colors
    
    Returns:
        list: List of filtered lines that contain any of the keywords
    """
    filtered_lines = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            # Simple progress reporting
            print(f"Processing {os.path.basename(file_path)}...")
            
            for line_number, line in enumerate(file, 1):
                # Check if any keyword pattern matches in the line
                if any(pattern.search(line) for pattern in keyword_patterns):
                    # Include filename and line number for reference
                    filename = os.path.basename(file_path)
                    filtered_lines.append((filename, line_number, line.strip()))
    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []
    
    return filtered_lines

def compile_keyword_patterns(keywords):
    """
    Compile regex patterns for each keyword for better performance.
    
    Args:
        keywords (list): List of keywords to search for
        
    Returns:
        list: List of compiled regex patterns
    """
    return [re.compile(re.escape(keyword), re.IGNORECASE) for keyword in keywords]

def extract_log_files_from_zip(zip_path, temp_dir):
    """
    Extract all LOG files from a ZIP file to a temporary directory.
    
    Args:
        zip_path (str): Path to the ZIP file
        temp_dir (str): Path to the temporary directory to extract files to
        
    Returns:
        list: List of paths to extracted LOG files
    """
    extracted_files = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get all file names in the ZIP
            file_list = zip_ref.namelist()
            
            # Filter for LOG files (case insensitive)
            log_files = [f for f in file_list if f.upper().endswith('.LOG')]
            
            if not log_files:
                print(f"No LOG files found in {os.path.basename(zip_path)}")
                return []
            
            print(f"Found {len(log_files)} LOG files in {os.path.basename(zip_path)}")
            
            # Extract only LOG files to temp directory
            for log_file in log_files:
                # Create directory structure if needed
                file_path = os.path.join(temp_dir, os.path.basename(log_file))
                zip_ref.extract(log_file, temp_dir)
                
                # Get the full path of the extracted file
                extracted_path = os.path.join(temp_dir, log_file)
                
                # Rename if file is in a subdirectory to avoid path issues
                if os.path.dirname(log_file):
                    new_path = os.path.join(temp_dir, os.path.basename(log_file))
                    if os.path.exists(new_path):
                        # Avoid name conflicts
                        base_name = os.path.splitext(os.path.basename(log_file))[0]
                        ext = os.path.splitext(log_file)[1]
                        new_path = os.path.join(temp_dir, f"{base_name}_{os.path.basename(zip_path)}{ext}")
                    
                    shutil.move(extracted_path, new_path)
                    extracted_path = new_path
                
                extracted_files.append(extracted_path)
                
    except zipfile.BadZipFile:
        print(f"Error: {os.path.basename(zip_path)} is not a valid ZIP file.")
    except Exception as e:
        print(f"Error extracting from ZIP file {os.path.basename(zip_path)}: {e}")
    
    return extracted_files

def process_all_log_files(folder_path, keywords, output_txt, output_html, highlight_words=None, process_zips=True):
    """
    Process all .LOG files in the specified folder and filter them based on keywords.
    Also processes LOG files within ZIP files if process_zips is True.
    
    Args:
        folder_path (str): Path to the folder containing the LOG files and/or ZIP files
        keywords (list): List of keywords to search for
        output_txt (str): Path to save all filtered lines as text
        output_html (str): Path to save all filtered lines as HTML with highlighting
        highlight_words (dict, optional): Dictionary mapping words to highlight colors
        process_zips (bool): Whether to process ZIP files containing LOG files
        
    Returns:
        dict: Dictionary with filenames as keys and lists of filtered lines as values
    """
    # Compile regex patterns once for better performance
    keyword_patterns = compile_keyword_patterns(keywords)
    
    # Find all log files in the specified folder
    log_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                if os.path.isfile(os.path.join(folder_path, f)) and f.upper().endswith('.LOG')]
    
    # Find all zip files in the specified folder if process_zips is True
    zip_files = []
    if process_zips:
        zip_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) 
                    if os.path.isfile(os.path.join(folder_path, f)) and f.upper().endswith('.ZIP')]
    
    if not log_files and not zip_files:
        print("No .LOG or .ZIP files found in the specified folder.")
        return {}
    
    print(f"Found {len(log_files)} .LOG files and {len(zip_files)} .ZIP files to process.")
    
    results = {}
    all_filtered_lines = []
    temp_dir = None
    
    try:
        # Create a temporary directory for ZIP extraction if needed
        if zip_files:
            temp_dir = tempfile.mkdtemp()
            print(f"Created temporary directory for ZIP extraction: {temp_dir}")
            
            # Process each ZIP file
            for zip_file in zip_files:
                print(f"Processing ZIP file: {os.path.basename(zip_file)}")
                extracted_logs = extract_log_files_from_zip(zip_file, temp_dir)
                
                # Add extracted LOG files to the list of files to process
                log_files.extend(extracted_logs)
        
        # Process all LOG files (both from the folder and extracted from ZIPs)
        for log_file_path in log_files:
            log_file = os.path.basename(log_file_path)
            
            # Get filtered lines for this file
            filtered_lines = filter_log_file(log_file_path, keyword_patterns, highlight_words)
            
            if filtered_lines:
                results[log_file] = filtered_lines
                all_filtered_lines.extend(filtered_lines)
                print(f"  Found {len(filtered_lines)} matching lines in {log_file}")
            else:
                print(f"  No matches found in {log_file}")
    
    finally:
        # Clean up the temporary directory if it was created
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Removed temporary directory: {temp_dir}")
    
    # Save all results to output files
    if all_filtered_lines:
        save_results_as_text(all_filtered_lines, output_txt)
        save_results_as_html(all_filtered_lines, output_html, highlight_words)
    
    return results

def highlight_text(text, highlight_words, html_mode=False):
    """
    Adds highlighting to text, either with ANSI colors (console) or HTML spans.
    
    Args:
        text (str): The text to highlight
        highlight_words (dict): Dictionary mapping words to highlight colors
        html_mode (bool): Whether to use HTML or ANSI formatting
        
    Returns:
        str: The highlighted text
    """
    result = text
    
    if not highlight_words:
        return result
        
    # Sort highlight words by length (longest first) to avoid partial matches
    if html_mode:
        # For HTML mode, prepare the text first
        result = result.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # Sort terms from longest to shortest to avoid partial matching
    sorted_items = sorted(highlight_words.items(), key=lambda x: len(x[0]), reverse=True)
    
    for word, color in sorted_items:
        pattern = None
        
        # Use word boundaries where appropriate
        if word.lower() in ["match", "mismatch"] and " " not in word:
            pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
        else:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
        
        if html_mode:
            # Determine CSS class
            css_class = ""
            if word.lower() == "match" and " " not in word:
                css_class = "match"
            elif word.lower() == "mismatch":
                css_class = "mismatch"
            elif "configuration" in word.lower():
                css_class = "configuration"
            else:
                css_class = "highlight"
            
            result = pattern.sub(f'<span class="{css_class}">\\g<0></span>', result)
        else:
            # Console highlighting with ANSI codes
            result = pattern.sub(f"{color}\\g<0>{Colors.RESET}", result)
    
    return result

def save_results_as_text(filtered_lines, output_file):
    """
    Save filtered lines to a text file.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as out_file:
            out_file.write(f"Total matches found: {len(filtered_lines)}\n")
            out_file.write("=" * 50 + "\n\n")
            
            for filename, line_number, content in filtered_lines:
                out_file.write(f"{filename} - Line {line_number}: {content}\n")
                
        print(f"\nAll filtered content saved to '{output_file}'")
    except Exception as e:
        print(f"Error writing to text output file: {e}")

def save_results_as_html(filtered_lines, output_file, highlight_words=None):
    """
    Save filtered lines to an HTML file with highlighting.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as out_file:
            # Write HTML header
            out_file.write("""<!DOCTYPE html>
<html>
<head>
    <title>LOG File Filtering Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .result-line { margin: 5px 0; padding: 5px; border-bottom: 1px solid #eee; font-family: monospace; white-space: pre-wrap; }
        .file-info { color: #555; font-weight: bold; }
        .match { background-color: #CCFFCC; color: #008800; font-weight: bold; }
        .mismatch { background-color: #FFCCCC; color: #CC0000; font-weight: bold; }
        .configuration { background-color: #CCE5FF; color: #0066CC; font-weight: bold; }
        .highlight { background-color: #FFFFCC; color: #888800; font-weight: bold; }
        .summary { margin: 20px 0; padding: 10px; background-color: #f0f0f0; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>LOG File Filtering Results</h1>
    <div class="summary">
        <p>Total matches found: """ + str(len(filtered_lines)) + """</p>
    </div>
""")
            
            # Write each result with highlighting
            for filename, line_number, content in filtered_lines:
                # Apply HTML highlighting
                html_content = highlight_text(content, highlight_words, html_mode=True)
                
                # Write the line
                out_file.write(f'    <div class="result-line">\n')
                out_file.write(f'        <span class="file-info">{filename} - Line {line_number}:</span> {html_content}\n')
                out_file.write(f'    </div>\n')
            
            # Write HTML footer
            out_file.write("""</body>
</html>""")
                
        print(f"HTML results with highlighting saved to '{output_file}'")
    except Exception as e:
        print(f"Error writing to HTML output file: {e}")

def load_config(config_file):
    """
    Load configuration from a JSON file or return default configuration.
    
    Args:
        config_file (str): Path to the configuration file
        
    Returns:
        tuple: (keywords, highlight_words)
    """
    default_keywords = ["CCP: EPK", "Configuration file:"]
    default_highlight = {
        "mismatch": Colors.RED,
        "match": Colors.GREEN,
        "Configuration file:": Colors.BLUE
    }
    
    if not config_file or not os.path.exists(config_file):
        return default_keywords, default_highlight
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        keywords = config.get('keywords', default_keywords)
        
        # Convert color strings to ANSI codes
        highlight_words = {}
        for word, color in config.get('highlight_words', {}).items():
            if color.upper() == "RED":
                highlight_words[word] = Colors.RED
            elif color.upper() == "GREEN":
                highlight_words[word] = Colors.GREEN
            elif color.upper() == "BLUE":
                highlight_words[word] = Colors.BLUE
            elif color.upper() == "YELLOW":
                highlight_words[word] = Colors.YELLOW
            else:
                highlight_words[word] = Colors.RESET
        
        return keywords, highlight_words
        
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return default_keywords, default_highlight

def create_default_config(config_file):
    """
    Create a default configuration file.
    
    Args:
        config_file (str): Path to the configuration file
    """
    default_config = {
        "keywords": ["CCP: EPK", "Configuration file:"],
        "highlight_words": {
            "mismatch": "RED",
            "match": "GREEN",
            "Configuration file:": "BLUE"
        }
    }
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4)
        print(f"Default configuration file created at '{config_file}'")
    except Exception as e:
        print(f"Error creating configuration file: {e}")

def main():
    """
    Main function to parse command line arguments and run the script.
    """
    parser = argparse.ArgumentParser(description='Filter and highlight content in LOG files.')
    parser.add_argument('-d', '--directory', default=".", 
                        help='Directory containing LOG files and/or ZIP files (default: current directory)')
    parser.add_argument('-o', '--output-prefix', default="filtered_log_results",
                        help='Prefix for output files (default: filtered_log_results)')
    parser.add_argument('-c', '--config', default="log_filter_config.json",
                        help='Configuration file path (default: log_filter_config.json)')
    parser.add_argument('--create-config', action='store_true',
                        help='Create a default configuration file and exit')
    parser.add_argument('--no-zip', action='store_true',
                        help='Skip processing ZIP files containing LOG files')
    
    args = parser.parse_args()
    
    # Create default config if requested
    if args.create_config:
        create_default_config(args.config)
        return
    
    # Load configuration
    keywords, highlight_words = load_config(args.config)
    
    # Check if config file exists, create it if not
    if not os.path.exists(args.config):
        print(f"Configuration file not found. Creating default at '{args.config}'")
        create_default_config(args.config)
    
    # Set output file paths
    output_txt = f"{args.output_prefix}.txt"
    output_html = f"{args.output_prefix}.html"
    
    # Process all LOG files (and ZIP files if --no-zip is not specified)
    results = process_all_log_files(args.directory, keywords, output_txt, output_html, 
                                  highlight_words, not args.no_zip)
    
    # Print summary and results with highlighting
    print("\nSummary:")
    if results:
        total_matches = sum(len(lines) for lines in results.values())
        print(f"Total of {total_matches} matches found across {len(results)} files.")
        print(f"Results saved to '{output_txt}' and '{output_html}'")
        
        # Display the first 10 results with highlighting in console
        if total_matches > 0:
            print("\nSample of results with highlighting:")
            count = 0
            for filename, result_lines in results.items():
                for f_name, line_number, content in result_lines:
                    highlighted_content = highlight_text(content, highlight_words)
                    print(f"{f_name} - Line {line_number}: {highlighted_content}")
                    count += 1
                    if count >= 10:
                        break
                if count >= 10:
                    print(f"\n...and {total_matches - 10} more results.")
                    break
    else:
        print("No matches found in any files.")

if __name__ == "__main__":
    main()