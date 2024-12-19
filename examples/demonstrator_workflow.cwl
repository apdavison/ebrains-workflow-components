#!/usr/bin/env cwl-runner
cwlVersion: v1.2
class: Workflow

label: Demonstrator workflow #001
doc: |
  This workflow demonstrates how to run a simple workflow, involving downloading experimental
  data from an EBRAINS dataset, running a sequence of data analysis steps with Elephant,
  then uploading the results to EBRAINS Bucket storage.

  The data analysis steps are:

  1. filter the recorded signal with a band-pass filter (Butterworth);
  2. perform a frequency analysis using a wavelet transform, and plot the result.

inputs:
  input_dataset:
    type: string
    label: "UUID of dataset containing input file"
  input_file:
    type: string
    label: "Path of input file containing sampled signals within dataset"
  input_format:
    type: string?
    label: "Format of the input data"
  token:
    type: string
    label: "EBRAINS IAM token for downloading from KG and uploading to Bucket"
  butterworth_output_file:
    type: string?
    label: "Output file for Butterworth filter"
  butterworth_output_format:
    type:
      type: enum
      symbols: ["NWBIO", "NixIO"]
    label: "Format of the Butterworth filter output file"
  highpass_frequency:
    type: string
    label: "High-pass cut-off frequency"
  lowpass_frequency:
    type: string
    label: "Low-pass cut-off frequency"
  order:
    type: int
    label: "Order of the Butterworth filter"
  filter_function:
    type:
      type: enum
      symbols: ["filtfilt", "lfilter", "sosfiltfilt"]
    label: "Filter function to use"
  block_idx:
    type: int?
    label: "Index of the block to process (default: 0)"
    default: 0
  segment_idx:
    type: int?
    label: "Index of the segment to process (default: 0)"
    default: 0
  analogsignal_idx:
    type: int?
    label: "Index of the analog signal to process (default: 0)"
    default: 0
  block_name:
    type: string?
    label: "Name of the block to process (optional)"
  action:
    type: string
    label: "Action on how to store the results with respect to the original data"
  wavelet_output_file_path:
    type: string
    label: "Output file for wavelet transform"
  frequency:
    type: string
    label: "Center frequency of the Morlet wavelet"
  n_cycles:
    type: float?
    label: "Size of the mother wavelet"
    default: 6.0
  sampling_frequency:
    type: float?
    label: "Sampling rate of the input data"
    default: 1.0
  zero_padding:
    type: boolean?
    label: "Specifies whether the data length is extended by padding zeros (default: True)"
    default: true
  start_time:
    type: float?
    label: "Start time of the signal slice in seconds"
    default: null
  stop_time:
    type: float?
    label: "Stop time of the signal slice in seconds"
    default: null
  output_folder:
    type: string
    label: "Output folder within Bucket"
  bucket_id:
    type: string
    label: ID of the bucket (collab) to which outputs should be uploaded

outputs:
  filtered_output_file:
    type: File
    outputSource: step_butterworth_filter/butterworth_output_file
  wavelet_output_file:
    type: File
    outputSource: step_wavelet_transform/wavelet_transform_output_file
  visualization_plots_pdf:
    type: File[]
    outputSource: step_wavelet_transform/visualization_plots_pdf
  remote_files:
    type:
      type: array
      items:
        type: record
        fields:
          location: string
          basename: string?
          checksum: string?
          size: long?
          format: string?
    outputSource: push_bucket/remote_files

steps:
  download_data:
    run: ../tools/kg/download_KG_datafile.cwl
    in:
      dataset_version_uuid: input_dataset
      datafile_path: input_file
      token: token
    out: [downloaded_data]

  step_butterworth_filter:
    run: ../tools/elephant/butterworth_filter.cwl
    in:
      input_file: download_data/downloaded_data
      input_format: input_format
      output_file: butterworth_output_file
      output_format: butterworth_output_format
      highpass_frequency: highpass_frequency
      lowpass_frequency: lowpass_frequency
      order: order
      filter_function: filter_function
      block_idx: block_idx
      block_name: block_name
      segment_idx: segment_idx
      analogsignal_idx: analogsignal_idx
      action: action
    out: [butterworth_output_file]

  step_wavelet_transform:
    run: ../tools/elephant/wavelet_transform.cwl
    in:
      input_file: step_butterworth_filter/butterworth_output_file
      input_format: butterworth_output_format
      output_file: wavelet_output_file_path
      frequency: frequency
      n_cycles: n_cycles
      sampling_frequency: sampling_frequency
      zero_padding: zero_padding
      start_time: start_time
      stop_time: stop_time
    out: [wavelet_transform_output_file, visualization_plots_pdf]

  push_bucket:
    run: ../tools/storage/bucket_push_file.cwl
    in:
      token: token
      bucket_id: bucket_id
      target_folder: output_folder
      files: step_wavelet_transform/visualization_plots_pdf
    out: [remote_files]



s:identifier: https://kg.ebrains.eu/api/instances/f907886f-39cd-405e-84fb-1b12fc5ef24f
s:keywords: ["data analysis"]
s:author:
  - class: s:Person
    s:identifier: https://orcid.org/0000-0001-7292-1982
    s:name: Moritz Kern
  - class: s:Person
    s:identifier: https://orcid.org/0000-0003-0503-5264
    s:name: Cristiano Köhler
  - class: s:Person
    s:identifier: https://orcid.org/0000-0002-4793-7541
    s:name: Andrew P. Davison
s:codeRepository: https://gitlab.ebrains.eu/workflows/components
s:version: "v0.1"
s:dateCreated: "2024-12-10"
s:programmingLanguage: Python

$namespaces:
 s: https://schema.org/

$schemas:
 - https://schema.org/version/latest/schemaorg-current-http.rdf
