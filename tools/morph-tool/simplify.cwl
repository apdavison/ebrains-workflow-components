#!/usr/bin/env cwl-runner
cwlVersion: v1.2

##### MORPH-TOOL #####
##### Simplify   #####
class: CommandLineTool
baseCommand: ["morph-tool", "simplify"]

stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/morph-tool

doc:
     - "Simplify the sections of a morphology"
     - "Detailed documentation: https://morph-tool.readthedocs.io/en/latest/index.html"

label: morph-tool-simplify

# The inputs for this process.
inputs:

  epsilon:
    type: float
    label: "Epsilon"
    inputBinding:
        position: 2
        prefix: "--epsilon"

  input_file:
    type: File
    label: "Input file to simplify"
    inputBinding:
        position: 3

  output_file:
    type: string
    inputBinding:
        position: 4

outputs:
  output_morph:
    type: File
    outputBinding:
        glob: "$(inputs.output_file)"

  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
