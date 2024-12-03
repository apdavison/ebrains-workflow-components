docker build -f ../tools/elephant/image/Dockerfile_pip -t elephant:latest tools/elephant/image
cwl-runner --debug ../tools/elephant/demonstrator_workflow.cwl inputs.yaml
