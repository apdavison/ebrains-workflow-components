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
    type: File
    label: "Output file for Butterworth filter"
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
  wavelet_output_file:
    type: string
    label: "Output file for wavelet transform"
  frequency:
    type: float
    label: "Center frequency of the Morlet wavelet"
  n_cycles:
    type: float?
    label: "Size of the mother wavelet"
    default: 6.0
  sampling_frequency:
    type: float?
    label: "Sampling rate of the input data"
    default: 1.0

outputs:
  filtered_output_file:
    type: File
    outputSource: step_butterworth_filter/output_file
  wavelet_output_file:
    type: File
    outputSource: step_wavelet_transform/output_file

steps:
  step_butterworth_filter:
    run: ./butterworth_filter.cwl
    in:
      input_file: input_file
      input_format: input_format
      highpass_frequency: highpass_frequency
      lowpass_frequency: lowpass_frequency
      order: order
      filter_function: filter_function
      output_file: butterworth_output_file
    out: [output_file]

  step_wavelet_transform:
    run: ./wavelet_transform.cwl
    in:
      input_file: step_butterworth_filter/output_file
      input_format: input_format
      output_file: wavelet_output_file
      frequency: frequency
      n_cycles: n_cycles
      sampling_frequency: sampling_frequency
    out: [output_file]