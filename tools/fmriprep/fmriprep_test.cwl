#!/usr/bin/env cwl-runner
cwlVersion: v1.2

class: CommandLineTool
baseCommand: ["bash", "fmriprep.sh"]

# Testcase DOI: doi:10.18112/openneuro.ds000254.v1.0.0

stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/fmriprep:esd

doc:
     - "doc"

label: fMRIPrep

# Create bash script to download data and run fMRIPrep
requirements:
  InitialWorkDirRequirement:
    listing:
      - entryname: fmriprep.sh
        entry: |-
          /bin/echo "Start Downloading data ..."
          /bin/bash "$1" # Download dataset from dataset download script
          /bin/echo "... End Downloading data"
          /bin/echo "Calling fMRIPrep ..."
          fmriprep "$2" "$3" "$4" "$5"


# Inputs
inputs:
  download_script:
    type: File
    label: "Dataset download script"
    inputBinding:
      position: 1
  bids_path:
    type: Directory
    label: "Input bids path"
    inputBinding:
      position: 2
  derivatives_path:
    type: Directory
    label: "Input derivative path"
    inputBinding:
      position: 3
  analysis_level:
    type: string
    inputBinding:
      position: 4
  named_options:
    type: string
    inputBinding:
      position: 5

# Outputs
outputs:
  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
