#!/usr/bin/env cwl-runner
cwlVersion: v1.2

class: CommandLineTool
baseCommand: bluepyefe_cli.py

stdout: o.txt
stderr: e.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/bluepyefe

doc:
     - "Extract batches of electrical features of experimental or simulated electrophysiology recordings using BluePyEfe and the eFel library."
     - "Functionality is provided via a command line interface to BluePyEfe."

label: bluepyefe-extract-electrical-neuron-features

# requirements:
#  - class: DockerRequirement
#    dockerOutputDirectory: "/home/denker/tmpdoc"  
#    dockerPull: docker-registry.ebrains.eu/workflow-components/bluepyefe

# The inputs for this process.
inputs:
  input_file_current:
    type: File
    label: "Input file for the electrical current."
    inputBinding:
      position: 1
      prefix: --input_file_current
  input_file_voltage:
    type: File
    label: "Input file for the electrical voltage."
    inputBinding:
      position: 2
      prefix: --input_file_voltage
  output_file:
    type: string
    inputBinding:
      position: 3
      prefix: --output_file
  features:
    type: string
    inputBinding:
      position: 4
      prefix: --features
  protocol_name:
    type: string
    inputBinding:
      position: 5
      prefix: --protocol_name
outputs:
#  output_statistics:
#    type: File
#    outputBinding:
#      # glob: "*.json"
#      glob: "$(inputs.output_file)"
  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
