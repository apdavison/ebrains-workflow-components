#!/usr/bin/env cwl-runner
cwlVersion: v1.2

class: CommandLineTool
baseCommand: wavelet_transform_cli.py

stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    #dockerImageId: docker-registry.ebrains.eu/workflow-components/elephant
    dockerImageId: elephant:latest

doc:
     - "Wavelet transform"
     - "Detailed function documentation: https://elephant.readthedocs.io/en/latest/reference/_toctree/signal_processing/elephant.signal_processing.wavelet_transform.html#elephant.signal_processing.wavelet_transform"

label: elephant-wavelet-transform

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
    type: string
    label: "Path to the output file"
    inputBinding:
      prefix: --output_file
  block_index:
    type: int?
    label: "Index of the block to process (default: 0)"
    default: 0
    inputBinding:
      prefix: --block_index
  block_name:
    type: string?
    label: "Name of the block to process (optional)"
    inputBinding:
      prefix: --block_name
  segment_index:
    type: int?
    label: "Index of the segment to process (default: 0)"
    default: 0
    inputBinding:
      prefix: --segment_index
  analog_signal_index:
    type: int?
    label: "Index of the analog signal to process (default: 0)"
    default: 0
    inputBinding:
      prefix: --analog_signal_index
  frequency:
    type: float?
    inputBinding:
      prefix: --frequency
    label: "Center frequency of the Morlet wavelet in Hz"
  visualization_plots:
    type: boolean?
    label: "Generate visualization plots for each input signal. It is averaged over channels (default: True)"
    default: true
    inputBinding:
      prefix: --visualization_plots
  n_cycles:
    type: float?
    label: "Size of the mother wavelet (default: 6.0)"
    default: 6.0
    inputBinding:
      prefix: --n_cycles
  sampling_frequency:
    type: float?
    label: "Sampling rate of the input data in Hz (default: 1.0)"
    default: 1.0
    inputBinding:
      prefix: --sampling_frequency
  zero_padding:
    type: boolean?
    label: "Specifies whether the data length is extended by padding zeros (default: True)"
    default: true
    inputBinding:
      prefix: --zero_padding

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