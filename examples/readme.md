# Running the Demonstrator Workflow

To run the workflow, follow these steps:

1. Ensure you have cwl-runner installed
2. Pull the latest Elephant Docker image:

   ```bash
   docker pull docker-registry.ebrains.eu/workflow-components/elephant:latest
   ```

3. Place the `.nix` file into the current directory. This workflow was tested with `l101210-001_small_cut_60.0s.nix`.
4. Prepare your `inputs.yaml` file with the required parameters for the workflow

5. Run the workflow using cwl-runner:

   ```bash
   cwl-runner ../tools/elephant/demonstrator_workflow.cwl inputs.yaml
   ```

6. The workflow will produce the following results, files:
    - `butterworth_output.nix`: The output file from the Butterworth filter process.
    - `output_wavelet.npz`: The output file from the Wavelet transform process.

## Requirements

- cwl-runner
- Docker
- Access to EBRAINS Docker registry
- Input data from r2g (`.nix`)

## Input Parameters

The input parameters should be specified in an `inputs.yaml` file.

## Troubleshooting

If you encounter issues:

1. Ensure Docker is running
2. Check your `inputs.yaml` file format
3. Run with --debug flag for detailed logging
