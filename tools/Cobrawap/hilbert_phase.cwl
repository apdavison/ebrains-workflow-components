#!/usr/bin/env cwl-runner
cwlVersion: v1.2

class: CommandLineTool
baseCommand: python hilbert_phase.py

stdout: o.txt
stderr: e.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/cobrawap

doc: 
     - "Detect trigger times (i.e., state transition / local wavefronts onsets) by finding crossing of a set phase-value in the channel signals."
     - "Functionality is provided via Stage 3 of the Cobrawap pipeline"

label: cobrawap-hilbert-phase

# requirements:
#  - class: DockerRequirement
#    dockerOutputDirectory: "/home/denker/tmpdoc"  
#    dockerPull: docker-registry.ebrains.eu/workflow-components/bluepyefe

# The inputs for this process.
inputs:
  input_file_current:
    type: File
    label: "This is the input file, which must be a Nix file containing a Neo Block."
    inputBinding:
      position: 1
      prefix: --data
#...
outputs:
  output_statistics:
    type: File
    outputBinding:
      # glob: "*.json"
      glob: "$(inputs.output_file)"
  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
