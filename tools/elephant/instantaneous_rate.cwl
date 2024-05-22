#!/usr/bin/env cwl-runner
cwlVersion: v1.2

class: CommandLineTool
baseCommand: instantaneous_rate_cli.py

stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/elephant

doc:
     - "Instantaneous firing rate estimation"
     - "Detailed function documentation: https://elephant.readthedocs.io/en/latest/reference/_toctree/statistics/elephant.statistics.instantaneous_rate.html#elephant.statistics.instantaneous_rate"

label: elephant-instantaneous-rate

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
  sampling_period:
    type: string
    label: "Time stamp resolution of the spike times, as a string in the form '<number> <unit>'"
    inputBinding:
      prefix: --sampling_period
  kernel:
    type: string
    label: "The string ‘auto’ or callable object of class kernels.Kernel (optional)"
    inputBinding:
      prefix: --kernel
    default: "auto"
  cutoff:
    type: float
    label: "This factor determines the cutoff of the probability distribution of the kernel (optional)"
    inputBinding:
      prefix: --cutoff
    default: 5.0
  t_start:
    type: string?
    label: "Start time of the interval used to compute the firing rate (optional), as a string in the form '<number> <unit>'"
    inputBinding:
      prefix: --t_start
  t_stop:
    type: string?
    label: "End time of the interval used to compute the firing rate (optional), as a string in the form '<number> <unit>'"
    inputBinding:
      prefix: --t_stop
  trim:
    type: boolean
    label: "Accounts for the asymmetry of a kernel (optional)"
    inputBinding:
      prefix: --trim
    default: false
  center_kernel:
    type: boolean
    label: "If set to True, the kernel will be centered on the spike (optional)"
    inputBinding:
      prefix: --center_kernel
    default: true
  border_correction:
    type: boolean
    label: "Apply a border correction to prevent underestimating the firing rates at the borders (optional)"
    inputBinding:
      prefix: --border_correction
    default: false
  pool_trials:
    type: boolean
    label: "If true, calculate firing rates averaged over trials (optional)"
    inputBinding:
      prefix: --pool_trials
    default: false
  pool_spike_trains:
    type: boolean
    label: "If true, calculate firing rates averaged over spike trains (optional)"
    inputBinding:
      prefix: --pool_spike_trains
    default: false
outputs:
  output_file:
    type: File
    outputBinding:
      glob: "$(inputs.output_file)"
  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
