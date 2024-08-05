#!/usr/bin/env cwl-runner
cwlVersion: v1.2

class: Workflow
baseCommand: fmriprep_test_workflow

# Testcase DOI: doi:10.18112/openneuro.ds000254.v1.0.0



stdout: stdout.txt
stderr: stderr.txt

doc:
     - "doc"

label: fMRIPrep-docker-wrapper-test-workflow


# The inputs for this process.
inputs:
  test_case_download_file: File

outputs:
  output_stdout: stdout
  output_stderr: stderr

requirements:
  - class: DockerRequirement
    dockerPull: docker-registry.ebrains.eu/workflow-components/fmriprep:pip
    dockerOutputDirectory: "/tmp/cwl-test" 
  # - class: InitialWorkDirRequirement
  #   listing:
  #     - $(inputs.code_folder)
  #     - $(inputs.outputs_folder)
  - class: InlineJavascriptRequirement
  - class: MultipleInputFeatureRequirement
  # InitialWorkDirRequirement:
  #   listing:
  #     - $(inputs.workdir)
  # 'sbg:license': CeCiLL
  # 'sbg:toolAuthor': Florent Bonnier


steps:

# Run test downloader
  download_test_case:
    run: download_test.cwl
    out: [test_case_folder]

# Run fMRIPrep test case
  run_test:
    run: run_test.cwl
