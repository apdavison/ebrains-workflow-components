#!/usr/bin/env cwl-runner
cwlVersion: v1.2

class: CommandLineTool
baseCommand: ["bash", "fmriprep_docker.sh"]




stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/fmriprep:pip

doc:
     - "doc"

label: fMRIPrep-docker-wrapper

requirements:
  NetworkAccess:
    networkAccess: true
  InitialWorkDirRequirement:
    listing:
      - entryname: fmriprep_docker.sh
        entry: |-
          # /bin/echo "Creating derivative directories in $3"
          # /bin/bash "mkdir -p $3" # Creating derivative directories
          /bin/echo "Downloading datasets in $2 ..."
          cd "$3"
          /bin/bash "$1" # Download dataset from dataset download script
          # datalad install -s "$6" "$2" # Download dataset from dataset download script
          cd ..
          ls "$3"
          /bin/echo "Download finished, inputs are in $2"
          /bin/echo "Start fMRIPrep $2 $3 $4"
          fmriprep "$2" "$3" "$4" "$5"
      - entry: $(inputs.derivatives_path)
        writable: true
      - entry: $(inputs.bids_path)
        writable: true


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
      position: 3
  derivatives_path:
    type: Directory
    label: "Input derivative path"
    inputBinding:
      position: 4
  analysis_level:
    type: string
    inputBinding:
      position: 5
  named_options:
    type: string?
    inputBinding:
      position: 2
outputs:
#  output_statistics:
#    type: File
#    outputBinding:
#      glob: "$(inputs.output_file)"
  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
  derivatives_path_output:
    type: Directory
    outputBinding:
      outputEval: $(inputs.derivatives_path)
  bids_path_output:
    type: Directory
    outputBinding:
      outputEval: $(inputs.bids_path)
