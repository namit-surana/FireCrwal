import json
import nbformat
from pathlib import Path

# Read the notebook
with open('scratch.ipynb', 'r') as f:
    nb = nbformat.read(f, as_version=4)

# Find the total_output variable
total_output = None
for cell in nb.cells:
    if cell.cell_type == 'code' and 'total_output' in cell.source:
        # Execute the relevant cells to get total_output
        exec_globals = {}
        try:
            exec(cell.source, exec_globals)
            if 'total_output' in exec_globals:
                total_output = exec_globals['total_output']
                break
        except:
            continue

# If we couldn't find it in code execution, look for it in outputs
if total_output is None:
    for cell in nb.cells:
        if cell.cell_type == 'code' and hasattr(cell, 'outputs'):
            for output in cell.outputs:
                if hasattr(output, 'data') and 'text/plain' in output.data:
                    text = output.data['text/plain']
                    if 'total_output' in text or isinstance(text, str) and text.startswith('['):
                        try:
                            # Try to parse as JSON
                            total_output = json.loads(text.strip("'\""))
                            break
                        except:
                            continue
            if total_output:
                break

if total_output is None:
    print("Could not find total_output in notebook. Let me check what variables are available...")
    # List all variables that might be the data we want
    for cell in nb.cells:
        if cell.cell_type == 'code':
            source = cell.source
            if any(keyword in source.lower() for keyword in ['json', 'output', 'result', 'data']):
                print(f"Found potential data in cell: {source[:100]}...")

else:
    print(f"Found total_output with {len(total_output)} items")
    
    # Create output directory
    output_dir = Path('output/split_json')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Split into 8 files
    items_per_file = len(total_output) // 8
    remainder = len(total_output) % 8
    
    start_idx = 0
    for i in range(8):
        # Calculate end index, adding one extra item to first 'remainder' files
        items_in_this_file = items_per_file + (1 if i < remainder else 0)
        end_idx = start_idx + items_in_this_file
        
        # Get the slice for this file
        file_data = total_output[start_idx:end_idx]
        
        # Write to JSON file
        output_file = output_dir / f'total_output_part_{i+1}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(file_data, f, ensure_ascii=False, indent=2)
        
        print(f"Created {output_file} with {len(file_data)} items")
        
        start_idx = end_idx

print("Done!")