#!/usr/bin/env cwl-runner
cwlVersion: v1.2

##### MORPH-TOOL #####
##### Convert    #####
class: CommandLineTool
baseCommand: ["morph-tool", "convert", "file"]

stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/morph-tool

doc:
     - "Convert Files"
     - "supported formats are ASC, SWC and H5"
     - "Detailed documentation: https://morph-tool.readthedocs.io/en/latest/index.html#converter"

label: morph-tool-convert-file

# The inputs for this process.
inputs:

  quiet:
    type: boolean
    label: "quiet"
    inputBinding:
        prefix: "--quiet"
        position: 2

  noquiet:
    type: boolean
    label: "no-quiet"
    inputBinding:
        prefix: "--no-quiet"
        position: 2

  nrn_order:
    type: boolean
    inputBinding:
        prefix: "--nrn-order"
        position: 2

  recenter:
    type: boolean
    inputBinding:
        prefix: "--recenter"
        position: 2

  single_point_soma:
    type: boolean
    inputBinding:
        prefix: "--single-point-soma"
        position: 2

  sanitize:
    type: boolean
    inputBinding:
        prefix: "--sanitize"
        position: 2

  ensure_NRN_area:
    type: boolean
    inputBinding:
        prefix: "--ensure-NRN-area"
        position: 2

  input_morph:
    type: File
    label: "Input File"
    inputBinding:
        position: 3

  output_morph:
    type: string
    label: "Output File"
    inputBinding:
        position: 4


outputs:

  output_file:
    type: File
    outputBinding:
      glob: "$(inputs.output_morph)"
    
  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
