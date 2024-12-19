# Running the Demonstrator Workflow

To run the workflow, follow these steps:

1. Ensure you have cwl-runner and a container management engine, such as Docker or Podman, installed.

2. Prepare your `inputs.yaml` file with the required parameters for the workflow.
   In particular, you will need to provide a valid EBRAINS auth token.
   This can be obtained from various places, such as the EBRAINS Lab or the KG Editor app.

3. Run the workflow using cwl-runner:

   ```bash
   cwl-runner demonstrator_workflow.cwl inputs.yaml
   ```

   If using podman:

   ```bash
   cwl-runner --podman demonstrator_workflow.cwl inputs.yaml
   ```

4. The workflow will produce the following results, files:
    - `butterworth_output.nix`: The output file from the Butterworth filter process.
    - `output_wavelet.npz`: The output file from the Wavelet transform process.
    - `wavelet_spectrum_{signal_index}.pdf` files containing the spectrum

## Requirements

- cwl-runner
- Docker or Podman
- Access to EBRAINS Docker registry

## Input Parameters

The input parameters should be specified in an `inputs.yaml` file.

## Troubleshooting

If you encounter issues:

1. Ensure Docker is running
2. Check your `inputs.yaml` file format
3. Run with --debug flag for detailed logging
