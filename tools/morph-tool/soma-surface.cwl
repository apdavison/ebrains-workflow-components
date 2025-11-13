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
     - "Get soma surface as computed by NEURON."
     - "Detailed documentation: https://morph-tool.readthedocs.io/en/stable/index.html#soma-intricacies"

label: morph-tool-soma-surface

# The inputs for this process.
inputs:
  
  quiet:
    type: boolean
    label: "quiet"
    inputBinding:
      position: 2
      prefix: "--quiet"

  noquiet:
    type: boolean
    label: "no-quiet"
    inputBinding:
      position: 2
      prefix: "--no-quiet"

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
