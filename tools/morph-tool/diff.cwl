#!/usr/bin/env cwl-runner
cwlVersion: v1.2

##### MORPH-TOOL #####
##### Diff       #####
class: CommandLineTool
baseCommand: ["morph-tool", "diff"]

stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/morph-tool

doc:
     - "Compare two morphologies"
     - "0 if morphologies are the same, else 1."
     - "Detailed documentation: https://morph-tool.readthedocs.io/en/latest/#morphology-diffing"

label: morph-tool-diff

# The inputs for this process.
inputs:

  rtol:
    type: float
    label: "relative tolerance"
    inputBinding:
      position: 3
      prefix: "--rtol"
  
  atol:
    type: float
    label: "absolute tolerance"
    inputBinding:
      position: 4
      prefix: "--atol"

  quiet:
    type: boolean
    label: "quiet"
    inputBinding:
      position: 5
      prefix: "--quiet"

  noquiet:
    type: boolean
    label: "no-quiet"
    inputBinding:
      position: 5
      prefix: "--no-quiet"

  input_file_morph1:
    type: File
    label: "First input morph file to compare with file2."
    inputBinding:
      position: 6
  input_file_morph2:
    type: File
    label: "Second input morph file to compare with file1."
    inputBinding:
      position: 7
      
outputs:
  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
