#!/usr/bin/env cwl-runner
cwlVersion: v1.2

class: CommandLineTool
baseCommand: extract_ephys_features_cli.py

stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/bluepyefe

doc:
     - "Extract batches of electrical features of experimental or simulated electrophysiology recordings using BluePyEfe and the eFel library."
     - "Functionality is provided via a command line interface to BluePyEfe."
     - "Detailed documentation: https://bluepyefe.readthedocs.io/en/latest/_autosummary/bluepyefe.extract.html"

label: bluepyefe-extract-ephys-features


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
  output_statistics:
    type: File
    outputBinding:
      glob: "$(inputs.output_file)"
  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
