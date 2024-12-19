cwlVersion: v1.0
class: CommandLineTool
baseCommand: download_KG_datafile.py
label: "Downloads a single file from a dataset identified by an EBRAINS KnowledgeGraph UUID."
hints:
  DockerRequirement:
    dockerPull: docker-registry.ebrains.eu/workflow-components/kg@sha256:0a23fb1c411efbe6a73069e1f90420a668fc5132e866b07f6df2f947296de184
requirements:
  InlineJavascriptRequirement: {}
inputs:
  token:
    type: string
    inputBinding:
      position: 1
      prefix: --token
  dataset_version_uuid:
    type: string
    inputBinding:
      position: 3
  datafile_path:
    type: string
    inputBinding:
      position: 4
outputs:
  downloaded_data:
    type: File
    outputBinding:
      glob: $('downloads/' + inputs.datafile_path)


s:identifier: https://kg.ebrains.eu/api/instances/17d470b8-44f9-4b75-b056-891447b1fd15
s:keywords: ["data transfer"]
s:author:
  - class: s:Person
    s:identifier: https://orcid.org/0000-0002-4793-7541
    s:name: Andrew P. Davison
s:codeRepository: https://gitlab.ebrains.eu/workflows/components
s:version: "v0.1"
s:dateCreated: "2024-12-10"
s:programmingLanguage: Python

$namespaces:
 s: https://schema.org/

$schemas:
 - https://schema.org/version/latest/schemaorg-current-http.rdf
