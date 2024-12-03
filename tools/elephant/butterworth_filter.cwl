#!/usr/bin/env cwl-runner
cwlVersion: v1.2

class: CommandLineTool
baseCommand: butterworth_filter_cli.py

stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/elephant:latest

doc:
     - "Butterworth filtering"
     - "Detailed function documentation: https://elephant.readthedocs.io/en/latest/reference/_toctree/signal_processing/elephant.signal_processing.butter.html"

label: elephant-butterworth-filter

# The inputs for this process.
inputs:
  input_file:
    type: File
    label: "A file, containing sampled signals, that can be read by Neo"
    inputBinding:
      prefix: --input_file
  input_format:
    type: string?
    label: "Format of the input data, as a Neo IO class name (optional; TODO: use openMINDS content-types instead?)"
    inputBinding:
      prefix: --input_format
  output_file:
    type: string?
    label: "Path to the output file"
    inputBinding:
      prefix: --output_file
  output_format:
    type:
      - "null"
      - type: enum
        symbols:
          - NWBIO
          - NixIO
    label: "Format of the output file (optional). If not provided, will be inferred from the output file suffix"
    inputBinding:
      prefix: --output_format
  highpass_frequency:
    type: string?
    label: "High-pass cut-off frequency (optional), as a string in the form '<number> <unit>', e.g. '5 kHz'"
    inputBinding:
      prefix: --highpass
  lowpass_frequency:
    type: string?
    label: "Low-pass cut-off frequency (optional), as a string in the form '<number> <unit>', e.g. '500 Hz'"
    inputBinding:
      prefix: --lowpass
  order:
    type: int?
    label: "Order of the Butterworth filter. Typical value: 4"
    inputBinding:
      prefix: --order
  filter_function:
    type:
      type: enum
      symbols:
        - filtfilt
        - lfilter
        - sosfiltfilt
    inputBinding:
      prefix: --filter_function
    label: "Filter function used"
  block_idx:
    type: int?
    label: "Index of the block to process (default: 0)"
    default: 0
    inputBinding:
      prefix: --block_idx
  segment_idx:
    type: int?
    label: "Index of the segment to process (default: 0)"
    default: 0
    inputBinding:
      prefix: --segment_idx
  analogsignal_idx:
    type: int?
    label: "Index of the analog signal to process (default: None)"
    default: 0
    inputBinding:
      prefix: --analogsignal_idx
  block_name:
    type: string?
    label: "Name of the block to process (optional)"
    inputBinding:
      prefix: --block_name
  action:
    type: string
    label: "Action on how to store the results with respect to the original data"
    inputBinding:
      prefix: --action
#  include:
#    type: string?
#    label: "A pseudo-Python expression that indicates which signals to process with the filter."
outputs:
  output_file:
    type: File
    outputBinding:
      glob: "$(inputs.output_file)"
  output_stdout:
    type: stdout
  output_stderr:
    type: stderr

requirements:
  InlineJavascriptRequirement: {}