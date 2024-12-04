#!/usr/bin/env cwl-runner
cwlVersion: v1.2
class: Workflow

inputs:
  input_file:
    type: File
    label: "Input file containing sampled signals"
  input_format:
    type: string?
    label: "Format of the input data"
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
steps:
  step_butterworth_filter:
    run: ./butterworth_filter.cwl
    in:
      input_file: input_file
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
    run: ./wavelet_transform.cwl
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