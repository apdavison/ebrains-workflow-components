#!/usr/bin/env cwl-runner
cwlVersion: v1.2

class: CommandLineTool
baseCommand: ['neurom', 'check']

stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/neurom:esd

doc:
     - "neurom check: performs checks on reconstructed morphologies from data contained in morphology files"
     - "Detailed function documentation: https://neurom.readthedocs.io/en/stable/morph_check.html"

label: neurom-check

# The inputs for this process.

  input_file_or_dir:
    type: File
    label: "A File or Directory, containing input morphology"
    inputBinding:
        position: 2
    
  config_file:
    type: File?
    label: "Configuration file"
    inputBinding:
      prefix: --config

  output_file:
    type: string
    label: "Path to the output file"
    inputBinding:
      prefix: --output

outputs:
  output_file:
    type: File
    outputBinding:
      glob: "$(inputs.output_file)"
  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
