#!/usr/bin/env cwltool

cwlVersion: v1.2
class: CommandLineTool
baseCommand: bucket_push_file.py
label: "Push a folder to an EBRAINS Collaboratory Bucket"
requirements:
  NetworkAccess:
     networkAccess: true
hints:
  DockerRequirement:
    dockerPull: docker-registry.ebrains.eu/workflow-components/storage@sha256:72f199ab788325bec1a4588789e85f908cbba34db9f46016dfbca5b03dd4dcc7
    #dockerPull: docker-registry.ebrains.eu/workflow-components/storage:local

inputs:
  bucket_id:
    type: string
    inputBinding:
      position: 1
  target_folder:
    type: string
    inputBinding:
      position: 2
  token:
    type: string
    inputBinding:
      position: 3
  files:
    type:
        type: array
        items: File
    inputBinding:
      position: 4

outputs:
  remote_files:
    type:
      type: array
      items:
        type: record
        fields:
          location: string
          basename: string?
          checksum: string?
          size: long?
          format: string?


s:identifier: https://kg.ebrains.eu/api/instances/459b415b-9b4a-4306-a69d-50b336d2510e
s:keywords: ["data transfer"]
s:author:
  - class: s:Person
    s:identifier: https://orcid.org/0000-0002-8306-0759
    s:name: Arnau Manasanch
  - class: s:Person
    s:identifier: https://kg.ebrains.eu/api/instances/714f39b8-9fd0-46cd-be4f-9112c87cfe3f
    s:name: Eleni Mathioulaki
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
