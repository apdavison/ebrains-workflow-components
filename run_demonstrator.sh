docker build -f tools/elephant/image/Dockerfile_pip -t elephant:latest tools/elephant/image
cwl-runner --debug tools/elephant/demonstrator_workflow.cwl inputs.yaml

# debug
# python tools/elephant/image/butterworth_filter_cli.py --input_file /home/kern/git/components/l101210-001_small_cut_60.0s.nix --input_format NixIO --highpass '5 Hz' --lowpass '30.0 Hz' --order 4 --filter_function filtfilt --output_file ./butterworth_output.nix --output_format "NixIO" --action "new"