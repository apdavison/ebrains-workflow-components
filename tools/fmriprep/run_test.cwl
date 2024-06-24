#!/usr/bin/env cwl-runner
cwlVersion: v1.2

class: CommandLineTool
baseCommand: fmriprep-docker

# Testcase DOI: doi:10.18112/openneuro.ds000254.v1.0.0



stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/fmriprep:pip

doc:
     - "doc"

label: fMRIPrep-docker-wrapper


# The inputs for this process.
inputs:
  bids_path:
    type: Directory
    label: "Input bids path"
    inputBinding:
      position: 1
  derivatives_path:
    type: Directory
    label: "Input derivative path"
    inputBinding:
      position: 2
  analysis_level:
    type: string
    inputBinding:
      position: 3

outputs:
#  output_statistics:
#    type: File
#    outputBinding:
#      glob: "$(inputs.output_file)"
  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
