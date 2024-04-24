import sys
import os
from cwltool.main import main


# Function to invoke cwl workflow files
def invoke_workflow(cwl_file, input_file):
    try:
        # Invoke the cwl workflow files using cwltool API
        result = main([cwl_file, input_file])
        print(f'Successfully completed cwl workflow: {cwl_file} with input: {input_file}')
    except Exception as e:
        print(f'Error occurred while running cwl workflow: {cwl_file} with input: {input_file}')
        print(str(e))
        result = 1
    return result


# Scanning all subdirectories of the folder "tools"
result = 0
for root, dirs, files in os.walk("tools"):
    if 'test' in dirs:
        test_dir = os.path.join(root, 'test')
        # If it finds a folder "test"
        input_files = [os.path.join(test_dir, file) for file in os.listdir(test_dir) if file.endswith('.yaml')]
        # Invoke the cwl workflow files within that folder, assuming one-to-one correspondence between workflow files and input files
        for input_file in input_files:
            workflow_file = os.path.join(root, os.path.basename(os.path.splitext(input_file)[0])) + '.cwl'
            result += invoke_workflow(workflow_file, input_file)
            # Fail fast
            if result != 0:
                sys.exit(result)

# Fail slow
#if result != 0:
#    sys.exit(result)
