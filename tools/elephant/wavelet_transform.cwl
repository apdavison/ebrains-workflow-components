#!/usr/bin/env cwl-runner
cwlVersion: v1.2

class: CommandLineTool
baseCommand: wavelet_transform_cli.py

stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/elephant@sha256:319c262d91f1a8d0ea1b9be70f6c705f85d9d61828d486d91de1fbf784d5cf36

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
    type:
      - "null"
      - type: enum
        symbols:
          - NWBIO
          - NixIO
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
    type: string?
    inputBinding:
      prefix: --frequency
    label: "Center frequency of the Morlet wavelet in Hz"
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
  start_time:
    type: float?
    label: "Start time of the signal slice in seconds"
    inputBinding:
      prefix: --start_time
  stop_time:
    type: float?
    label: "Stop time of the signal slice in seconds"
    inputBinding:
      prefix: --stop_time

outputs:
  wavelet_transform_output_file:
    type: File
    outputBinding:
      glob: "$(inputs.output_file)"
  visualization_plots_pdf:
    type: File[]
    outputBinding:
      glob: "*.pdf"
  output_stdout:
    type: stdout
  output_stderr:
    type: stderr

requirements:
  InlineJavascriptRequirement: {}



s:identifier: https://kg.ebrains.eu/api/instances/2f3c47fb-c267-43d0-afa1-b4e04898f8f2
s:keywords: ["data analysis"]
s:author:
  - class: s:Person
    s:identifier: https://orcid.org/0000-0001-7292-1982
    s:name: Moritz Kern
  - class: s:Person
    s:identifier: https://orcid.org/0000-0003-0503-5264
    s:name: Cristiano Köhler
s:codeRepository: https://gitlab.ebrains.eu/workflows/components
s:version: "v0.1"
s:dateCreated: "2024-12-10"
s:programmingLanguage: Python

$namespaces:
 s: https://schema.org/

$schemas:
 - https://schema.org/version/latest/schemaorg-current-http.rdf
