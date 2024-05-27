#!/usr/bin/env cwl-runner
cwlVersion: v1.2

class: CommandLineTool
baseCommand: ['neurom', 'view']

stdout: stdout.txt
stderr: stderr.txt

hints:
  DockerRequirement:
    dockerImageId: docker-registry.ebrains.eu/workflow-components/neurom:esd

doc:
     - "neurom view: draw morphologies"
     - "Detailed function documentation: neurom view --help"

label: neurom-check

# The inputs for this process.

  input_file:
    type: File
    label: "A File containing input morphology"
    inputBinding:
        position: 2
    
  plane:
# xy|yx|yz|zy|xz|zx
    type:
      type: enum
      symbols:
        - xy
        - yx
        - yz
        - zy
        - xz
        - zx
    label: "Viewing plane"
    inputBinding:
      prefix: --plane
      position: 1

  backend:
# matplotlib | plotly
    type:
      type: enum
      symbols:
        - matplotlib
        - plotly
    label: "Backend"
    inputBinding:
      prefix: --backend
      position: 1

  realistic-diameters:
    type: boolean?
    label: "Scale diameters"
    inputBinding:
      prefix: --realistic-diameters
      position: 1

  dim:
    type: boolean?
    inputBinding:
      position: 1
      prefix: --3d

outputs:
  output_stdout:
    type: stdout
  output_stderr:
    type: stderr
