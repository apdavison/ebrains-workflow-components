#!/usr/bin/env cwl-runner
cwlVersion: v1.2

##### MORPH-TOOL #####
##### Convert    #####
class: CommandLineTool
baseCommand: ["morph-tool", "convert", "folder"]

stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/morph-tool

doc:
     - "Convert directories"
     - "supported formats are ASC, SWC and H5"
     - "all files can be converted within a directory"
     - "Detailed documentation: https://morph-tool.readthedocs.io/en/latest/index.html#converter"

label: morph-tool-convert-folder

# The inputs for this process.
inputs:

  output_format:
    type:
      type: enum
      symbols:
        - SWC
        - ASC
        - H5
    inputBinding:
      prefix: -ext

  nrn_order:
    type: boolean
    inputBinding:
      prefix: --nrn-order

  recenter:
    type: boolean
    inputBinding:
      prefix: --recenter

  input_morph:
    type:
      - Directory
      - File
    label: "Input File/Directory"

  output_morph:
    type:
      - File
      - Directory
    label: "Output File/Directory"


outputs:
  # output_morph:
    

  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
