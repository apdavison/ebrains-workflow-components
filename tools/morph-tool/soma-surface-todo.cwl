#!/usr/bin/env cwl-runner
cwlVersion: v1.2

##### MORPH-TOOL #####
##### Soma-Surface  #####
class: CommandLineTool
baseCommand: ["morph-tool", "soma-surface"]

stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/morph-tool

doc:
     - ""
     - "Detailed documentation: https://morph-tool.readthedocs.io/en/latest/#morphology-diffing"

label: morph-tool-soma-surface

# The inputs for this process.
inputs:
  input_file:
    type: File
    label: "input morph file"
    inputBinding:
      position: 3
outputs:
  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
