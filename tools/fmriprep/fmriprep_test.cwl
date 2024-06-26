#!/usr/bin/env cwl-runner
cwlVersion: v1.2

class: CommandLineTool
baseCommand: ["bash", "fmriprep_docker.sh"]

# Testcase DOI: doi:10.18112/openneuro.ds000254.v1.0.0



stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/fmriprep:pip

doc:
     - "doc"

label: fMRIPrep-docker-wrapper

requirements:
  InitialWorkDirRequirement:
    listing:
      - entryname: fmriprep_docker.sh
        entry: |-
          /bin/bash "$1" # Download dataset from dataset download script 
          fmriprep-docker "$2" "$3" "$4" "$5"


# The inputs for this process.
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
outputs:
#  output_statistics:
#    type: File
#    outputBinding:
#      glob: "$(inputs.output_file)"
  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
