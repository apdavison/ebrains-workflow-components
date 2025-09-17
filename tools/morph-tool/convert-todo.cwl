#!/usr/bin/env cwl-runner
cwlVersion: v1.2

##### MORPH-TOOL #####
##### Convert    #####
class: CommandLineTool
baseCommand: ["morph-tool", "convert"]

stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/morph-tool

doc:
     - "Convert files or directories"
     - "supported formats are ASC, SWC and H5"
     - "a single file can be converted or all files within a directory"
     - "Detailed documentation: https://morph-tool.readthedocs.io/en/latest/index.html#converter"

label: morph-tool-convert

# The inputs for this process.
inputs:
  input_type:
    type:
      type: enum
      symbols:
        - file
        - folder
    label: "Input type. file or directory"

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
  output_morph:
    

  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
