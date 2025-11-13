#!/usr/bin/env cwl-runner
cwlVersion: v1.2

##### MORPH-TOOL #####
##### Test Workflow  #####
## Test the component on exactly same files ##
class: Workflow

# hints:
#   DockerRequirement:
#     dockerImageId: docker-registry.ebrains.eu/workflow-components/morph-tool

doc:
     - "Test the component on exactly same files"

label: morph-tool-test-workflow

# The inputs for this process.
inputs:

  input_file_morph1: File
  
  input_file_morph2: File?

  rtol: float
  
  atol: float

  quiet: boolean

  noquiet: boolean
  
  epsilon: float

  output_file: string

  output_format: string

  nrn_order: boolean

  recenter: boolean

  single_point_soma: boolean

  sanitize: boolean
  
  ensure_NRN_area: boolean

  ncores: int
  

steps:
    test-diff:
        run: ../diff.cwl
        in:
            input_file_morph1: input_file_morph1
            input_file_morph2: input_file_morph2
            rtol: rtol
            atol: atol
            quiet: quiet
            noquiet: noquiet
        out: [output_stdout, output_stderr]

    test-simplify:
        run: ../simplify.cwl
        in: 
            epsilon: epsilon
            input_file: input_file_morph1
            output_file: output_file
        out: [output_morph, output_stdout, output_stderr]

    test-soma-surface:
        run: ../soma-surface.cwl
        in:
            quiet: quiet
            noquiet: noquiet
            input_file: input_file_morph1
        out: [output_stdout, output_stderr]

    test-convert-file:
        run: ../convert-file.cwl
        in:
            quiet: quiet
            noquiet: noquiet
            nrn_order: nrn_order
            recenter: recenter
            single_point_soma: single_point_soma
            sanitize: sanitize
            ensure_NRN_area: ensure_NRN_area
            input_morph: input_file_morph1
            output_morph: output_file
        
        out: [output_stdout, output_stderr, output_file]

    # test-convert-folder:
    #     run: ../convert-folder.cwl
    #     in:
    #         output_format: output_format
    #         quiet: quiet
    #         noquiet: noquiet
    #         nrn_order: nrn_order
    #         recenter: recenter
    #         single_point_soma: single_point_soma
    #         sanitize: sanitize
    #         ensure_NRN_area: ensure_NRN_area
    #         ncores: ncores
    #         input_morph: input_file_morph1
    #         output_morph: output_file
        
    #     out: [output_stdout, output_stderr, output_dir]

outputs:
    output_morph_simplify:
        type: File
        outputSource: test-simplify/output_morph
    output_morph_convert_file:
        type: File
        outputSource: test-convert-file/output_file

    diff_stdout:
        type: File
        outputSource: test-diff/output_stdout
    diff_stderr:
        type: File
        outputSource: test-diff/output_stderr

    simplify_stdout:
        type: File
        outputSource: test-simplify/output_stdout
    simplify_stderr:
        type: File
        outputSource: test-simplify/output_stderr

    soma_surface_stdout:
        type: File
        outputSource: test-soma-surface/output_stdout
    soma_surface_stderr:
        type: File
        outputSource: test-soma-surface/output_stderr

    convert_file_stdout:
        type: File
        outputSource: test-convert-file/output_stdout
    convert_file_stderr:
        type: File
        outputSource: test-convert-file/output_stderr
    # output_dir_convert_folder:
    #     type: Directory
    #     outputSource: test-convert-folder/output_dir

