"""
Script to convert a CWL provenance Research Object to a JSON file that can be uploaded to the EBRAINS Prov API

Copyright Andrew Davison, CNRS, 2022, 2023, 2025
"""

import argparse
import sys
import os
import re
import json
import subprocess
from pprint import pprint
from datetime import datetime
from itertools import chain
from rdflib import Graph, RDF, URIRef
from rdflib.namespace import FOAF, PROV, RDFS
import requests


DEFAULT_CONTAINER_ENGINE = "docker"


def guess_content_type(file_name):
    # todo: use a KG query to create the lookup
    lookup = {
        ".mat": "application/5-mat",
        ".png": "image/png",
        ".json": "application/json",
        ".pdf": "application/pdf",
        ".py": "text/x-python",
        ".md": "text/markdown",
        ".txt": "text/plain",
        ".html": "text/html",
        ".pkl": "application/vnd.pickle",
        ".nix": "application/vnd.g-node.nix+hdf5",
        ".ns2": "application/vnd.blackrockmicrosystems.neuralsignals.2"
    }
    base, ext = os.path.splitext(file_name)
    return lookup.get(ext, None)

valid_computation_types = ("data transfer", "simulation", "data analysis", "visualization", "optimization")

def guess_computation_type(label, plan):
    if "https://schema.org/keywords" in plan:
        for ct in valid_computation_types:
            if ct in plan["https://schema.org/keywords"]:
                return ct
    if "analysis" in label:
        return "data analysis"
    elif "visuali" in label:
        return "visualization"
    else:
        return None


def get_container_engine_version(container_engine=DEFAULT_CONTAINER_ENGINE):
    proc = subprocess.run([container_engine, "--version"], check=True, capture_output=True, text=True)
    match = re.match(r"version (?P<version>[0-9\.]+), build \w+", proc.stdout)
    if match:
        return match["version"]


def get_software_version_from_container(image, command_name, container_engine=DEFAULT_CONTAINER_ENGINE):
    cmd = [container_engine, "run", "-it", str(image), command_name, "--version"]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    match = re.match(fr"\w+ (?P<version>[0-9\.]+)", proc.stdout)
    if match:
        return match["version"]


def get_container_system_info(container_engine=DEFAULT_CONTAINER_ENGINE):
    cmd = [container_engine, "system", "info", "--format", "'{{json .}}'"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(proc.stdout[1:-2])
    if container_engine == "docker":
        return {
            key: data[key]
            for key in ("KernelVersion", "OperatingSystem", "OSType", "Architecture", "NCPU", "MemTotal")
        }
    elif container_engine == "podman":
        h = data["host"]
        return {
            "KernelVersion": h["kernel"],
            "OperatingSystem": f"{h['distribution']['distribution']} {h['distribution']['version']}",
            "OSType": h["os"],
            "Architecture": h["arch"],
            "NCPU": h["cpus"],
            "MemTotal": h["memTotal"]

        }
    else:
        raise ValueError("Only 'docker' and 'podman' supported for now")
    return data


def get_python_dependencies(image, container_engine=DEFAULT_CONTAINER_ENGINE):
    cmd = [container_engine, "run", str(image), "pip", "freeze"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    deps = {}
    for line in proc.stdout.splitlines():
        if "==" in line:
            name, ver = line.split("==")
        elif "@" in line:
            name, ver = line.split("@")[0].strip(), "unknown"
        deps[name] = ver
    return deps


def as_cmdline_string(obj):
    if isinstance(obj, list):
        return " ".join(str(item) for item in obj)
    else:
        return str(obj)

def uuid_from_uri(uri):
    if uri.startswith("http"):
        return uri.split("/")[-1]
    else:
        return uri


def add_file_locations(stages, prov_dir):
    location_map = {}
    for stage in stages:
        for item in chain(stage["input"], stage["output"]):
            if "kg_download_manifest.json" in item.get("file_name", ""):
                hash_val = item["hash"]["value"]
                prov_copy_path = f"{prov_dir}/data/{hash_val[:2]}/{hash_val}"
                with open(prov_copy_path) as fp:
                    location_map.update(json.load(fp))

    # now look for file names that match the location map
    for stage in stages:
        for item in chain(stage["input"], stage["output"]):
            if "file_name" in item:
                for name, location in location_map.items():
                    if item["file_name"] == name:
                        assert item["location"] is None
                        item["location"] = location


hash_alg_lookup = {
    "sha1": "SHA-1"
}



class File:

    def __init__(self, node, graph, role=None, creation_time=None, dir_name=None):
        self.node = node
        self.g = graph
        self.role = role
        self.creation_time = creation_time
        self.dir_name = dir_name

    def to_json(self, prov_dir):
        entity_value = self.g.value(self.node, URIRef("https://w3id.org/cwl/prov#basename"))
        entity_detail = self.g.value(subject=self.node, predicate=PROV.specializationOf)
        hash_alg, hash_val = str(entity_detail).split(":")[3:5]
        hash =  {
            "algorithm": hash_alg_lookup[hash_alg],
            "value": hash_val
        }
        prov_copy_path = f"{prov_dir}/data/{hash_val[:2]}/{hash_val}"
        file_size = os.stat(prov_copy_path).st_size

        data = {
            "file_name": str(entity_value),
            "hash": hash,
            "size": file_size
        }
        if self.dir_name:
            data["file_name"] = f"{self.dir_name}/{entity_value.value}"
        if self.role:
            data["role"] = self.role
        if self.creation_time:
            data["creation_time"] = self.creation_time
        return data


class Folder:

    def __init__(self, node, graph, parent_dir_name=None):
        self.node = node
        self.g = graph
        if parent_dir_name:
            self.dir_name = os.path.join(parent_dir_name, self._get_folder_name(node))
        else:
            self.dir_name = None

    def _get_folder_name(self, subnode):
        key_entity_pair = list(self.g.subjects(PROV.pairEntity, subnode))[0]
        return list(self.g.objects(key_entity_pair, PROV.pairKey))[0].value

    def to_json(self, prov_dir):
        contents = []
        for _entity in self.g.objects(self.node, PROV.hadMember):
            entity_types = list(self.g.objects(_entity, RDF.type))
            if URIRef("http://purl.org/wf4ever/wf4ever#File") in entity_types:
                _file = File(_entity, self.g, dir_name=self.dir_name)
                contents.append(_file.to_json(prov_dir))
            elif URIRef("http://purl.org/wf4ever/ro#Folder") in entity_types:
                sub_dir_name = self._get_folder_name(_entity)
                if self.dir_name:
                    dir_name = os.path.join(self.dir_name, sub_dir_name)
                else:
                    dir_name = sub_dir_name
                for _member_node in self.g.objects(_entity, PROV.hadMember):
                    sub_entity_types = list(self.g.objects(_member_node, RDF.type))
                    if URIRef("http://purl.org/wf4ever/wf4ever#File") in sub_entity_types:
                        # input/output is a File
                        _file = File(_member_node, self.g, dir_name=dir_name)
                        contents.append(_file.to_json(prov_dir))
                    elif URIRef("http://purl.org/wf4ever/ro#Folder") in sub_entity_types:
                        # input is a Directory
                        "http://www.openarchives.org/ore/terms/isDescribedBy"  # points to an external .ttl file with dir contents
                        "http://www.w3.org/ns/prov#hadDictionaryMember"
                        "http://www.w3.org/ns/prov#hadMember"  # <--- use this
                        "http://www.w3.org/ns/prov#qualifiedGeneration"
                        _folder = Folder(_member_node, self.g, parent_dir_name=dir_name)
                        contents.extend(_folder.to_json(prov_dir))
            else:
                contents.append(
                    self.g.value(_entity, PROV.value).value
                )
        return contents


class Dictionary:

    def __init__(self, node, graph, role=None):
        self.node = node
        self.g = graph
        self.role = role

    def to_json(self):
        data = {}
        for _ref in self.g.objects(self.node, PROV.hadDictionaryMember):
            pairent = list(self.g.objects(_ref, PROV.pairEntity))[0]
            key = self.g.value(_ref, PROV.pairKey).value
            value = self.g.value(pairent, PROV.value).value
            data[key] = value
        if self.role:
            data["role"] = self.role
        return data


class Stage:

    def __init__(self, node, graph, prov_dir):
        self.node = node
        self.g = graph
        self.prov_dir = prov_dir

    def _get_folder_name(self, subnode):
        key_entity_pair = list(self.g.subjects(PROV.pairEntity, subnode))[0]
        return list(self.g.objects(key_entity_pair, PROV.pairKey))[0].value

    @property
    def label(self):
        return str(self.g.value(self.node, RDFS.label))

    @property
    def start_time(self):
        _qstart = self.g.value(self.node, PROV.qualifiedStart)
        return datetime.fromisoformat(self.g.value(_qstart, PROV.atTime))

    @property
    def end_time(self):
        _qend = self.g.value(self.node, PROV.qualifiedEnd)
        return datetime.fromisoformat(self.g.value(_qend, PROV.atTime))

    def _handle_io_object(self, collection, _entity, role, creation_time=None):
        entity_types = list(self.g.objects(_entity, RDF.type))
        if URIRef("http://purl.org/wf4ever/wf4ever#File") in entity_types:
            # input/output is a File
            _file = File(_entity, self.g, role=role, creation_time=creation_time)
            collection.append(_file.to_json(self.prov_dir))
        elif URIRef("http://purl.org/wf4ever/ro#Folder") in entity_types:
            # input is a Directory
            "http://www.openarchives.org/ore/terms/isDescribedBy"  # points to an external .ttl file with dir contents
            "http://www.w3.org/ns/prov#hadDictionaryMember"
            "http://www.w3.org/ns/prov#hadMember"  # <--- use this
            "http://www.w3.org/ns/prov#qualifiedGeneration"
            _folder = Folder(_entity, self.g)
            collection.append({
                "role": role,
                "contents": _folder.to_json(self.prov_dir)
            })
        elif URIRef("http://www.w3.org/ns/prov#Dictionary") in entity_types:
            _dict = Dictionary(_entity, self.g, role=role)
            collection.append(_dict.to_json(self.prov_dir))
        elif URIRef("http://www.w3.org/ns/prov#Collection") in entity_types:
            # input/output is a list
            contents = []
            for _sub_entity in self.g.objects(_entity, PROV.hadMember):
                self._handle_io_object(contents, _sub_entity, role=role, creation_time=creation_time)
            collection.append({
                "role": role,
                "value": contents
            })
        else:
            # input/output is a simple type
            value = self.g.value(_entity, PROV.value)
            if value is not None:
                value = value.value
            collection.append({
                "role": role,
                "value": value
            })
        return collection

    @property
    def inputs(self):
        _inputs = []
        for _qusage in self.g.objects(self.node, PROV.qualifiedUsage):
            role = "#" + str(self.g.value(_qusage, PROV.hadRole)).split("#")[1]
            _entity = self.g.value(_qusage, PROV.entity)
            self._handle_io_object(_inputs, _entity, role=role)
        return _inputs

    @property
    def outputs(self):
        _outputs = []
        for _gen in self.g.subjects(PROV.activity, self.node):
            role = "#" + str(self.g.value(subject=_gen, predicate=PROV.hadRole)).split("#")[1]
            creation_time = self.g.value(subject=_gen, predicate=PROV.atTime)
            _entity= self.g.value(predicate=PROV.qualifiedGeneration, object=_gen)
            self._handle_io_object(_outputs, _entity, role=role, creation_time=creation_time)
        return _outputs

    @property
    def execution(self):
        _associations = self.g.objects(self.node, PROV.wasAssociatedWith)
        execution_items = []
        for _assoc in _associations:
            if PROV.SoftwareAgent in self.g.objects(_assoc, RDF.type):
                process_label = self.g.value(_assoc, RDFS.label)
                process_image = self.g.value(_assoc, URIRef("https://w3id.org/cwl/prov#image"))
            else:
                raise NotImplementedError
            execution_items.append({
                "label": process_label,
                "image": process_image
            })
        return execution_items

    @property
    def plan_id(self):
        _qassoc = list(self.g.objects(self.node, PROV.qualifiedAssociation))[0]
        plan_ref = self.g.value(_qassoc, PROV.hadPlan)
        return "#" + str(plan_ref).split("#")[1]


def get_prov_for_stage(stage, plan_usage, plan_implementation, container_engine=DEFAULT_CONTAINER_ENGINE):
    inputs = []
    inputs_json = {}
    def _handle_input_item(item):
        if item["role"].startswith(plan_usage["id"]):
            key = item["role"].split("/")[-1]
        else:
            raise Exception("unexpected")
        if "contents" in item:
            for file_obj in item["contents"]:
                inputs.append({
                    "description": item["role"],
                    "file_name": file_obj["file_name"],
                    "format": guess_content_type(file_obj["file_name"]),
                    "hash": file_obj.get("hash", None),
                    "location": None,  # todo: if possible, figure out public URL
                    "size": file_obj.get("size", None)   # as for hash
                })
            # todo: add entry to inputs_json?
        elif "value" in item:
            # could be a model UUID, what else? software?
            # todo: check if the value is a UUID
            if "model" in key:
                inputs.append({"model_version_id": item["value"]})
                inputs_json[key] = item["value"]
            elif key == "dataset_version_uuid":
                path_key = None
                for _item in stage.inputs:
                    if "datafile_path" in _item["role"]:
                        path_key = _item["value"]
                        break
                if path_key:
                    inputs.append({
                        "dataset_version_id": item["value"],
                        "datafile_path": path_key
                    })
                else:
                    inputs.append({"dataset_version_id": item["value"]})
                inputs_json[key] = item["value"]
            elif isinstance(item["value"], list):
                for subitem in item["value"]:
                    _handle_input_item(subitem)
            else:
                inputs_json[key] = item["value"]
        elif "file_name" in item:
            inputs.append({
                "description": item["role"],
                "file_name": item["file_name"],
                "format": guess_content_type(item["file_name"]),
                "hash": item.get("hash", None),
                "location": None,  # todo: if possible, figure out public URL
                "size": item.get("size", None)   # as for hash
            })
            if key in inputs_json:
                inputs_json[key].append(item["file_name"])
            else:
                inputs_json[key] = item["file_name"]
        else:
            raise Exception("2")
    for item in stage.inputs:
        _handle_input_item(item)

    outputs = []
    outputs_json = {}
    def _handle_output_item(item):
        if item["role"].startswith(plan_usage["id"]):
            key = item["role"].split("/")[-1]
        else:
            raise Exception("unexpected")
        if "file_name" in item:
            outputs.append({
                "description": key,
                "file_name": item["file_name"],
                "format": guess_content_type(item["file_name"]),
                "hash": item["hash"],
                "location": None,  # todo: if possible, figure out public URL
                "size": item["size"]
            })
        elif "location" in item:
            if "checksum" in item:
                hash_alg, hash_val = item["checksum"].split("$")
                hash = {
                    "algorithm": hash_alg_lookup[hash_alg],
                    "value": hash_val,
                }
            else:
                hash = None
            outputs.append({
                "description": key,
                "file_name": item["basename"],
                "format": item["format"] or guess_content_type(item["basename"]),
                "hash": hash,
                "location": item["location"],
                "size": item["size"]
            })
        else:
            if "contents" in item:
                if isinstance(item["contents"][0], dict):
                    for subitem in item["contents"]:
                        if "file_name" in subitem:
                            outputs.append({
                                "description": key,
                                "file_name": subitem["file_name"],
                                "format": guess_content_type(subitem["file_name"]),
                                "hash": subitem.get("hash", None),
                                "location": None,  # todo: if possible, figure out public URL
                                "size": subitem["size"]
                            })
                else:
                    outputs_json[key] = item["contents"]
            elif "value" in item:
                if isinstance(item["value"], list):
                    for subitem in item["value"]:
                        _handle_output_item(subitem)
                elif isinstance(item["value"], str) and item["value"].startswith("http"):
                    outputs.append({
                        "location": item["value"]
                    })
                outputs_json[key] = item["value"]
            else:
                raise NotImplementedError
    for item in stage.outputs:
        _handle_output_item(item)

    # command-line arguments
    arg_prefixes = {}
    expected_args = []
    for input in sorted([item for item in plan_implementation["inputs"] if "inputBinding" in item],
                        key=lambda item: item["inputBinding"].get("position", 0)):
        # default "position" is 0
        # see https://www.commonwl.org/user_guide/topics/inputs.html#essential-input-parameters
        arg_name = input["id"].split("/")[-1]
        expected_args.append(arg_name)
        if "prefix" in input["inputBinding"]:
            arg_prefixes[arg_name] = input["inputBinding"]["prefix"]
    provided_args = inputs_json
    if "token" in provided_args:
        provided_args["token"] = "<MASKED SECRET>"
    if plan_implementation["baseCommand"] == "python":
        args = []
    else:
        args = [plan_implementation["baseCommand"]]
    for arg_name in expected_args:
        try:
            arg = provided_args[arg_name]
        except KeyError:
            pass  # for now
        else:
            if arg_name in arg_prefixes:
                arg = f"{arg_prefixes[arg_name]} {arg}"
            if isinstance(arg, list):
                args.extend(arg)
            else:
                args.append(arg)

    # execution environment
    docker_requirement = [
        item for item in plan_implementation["hints"]
        if item["class"] == "DockerRequirement"
    ][0]
    docker_info = get_container_system_info(container_engine)
    docker_image = docker_requirement.get("dockerPull", docker_requirement.get("dockerImageId"))
    software = [{
        "software_name": "Python",
        "software_version": get_software_version_from_container(docker_image, "python", container_engine)
    }]
    for name, ver in get_python_dependencies(docker_image, container_engine).items():
        software.append({
            "software_name": name,
            "software_version": ver
        })
    env = {
        "name": docker_image,
        "hardware": "generic",
        "configuration": {
            key: docker_info[key]
            for key in ("KernelVersion", "OperatingSystem", "OSType", "Architecture", "NCPU", "MemTotal")
        },
        "software": software,
        "description": "Docker container"
    }

    return {
        "description": plan_implementation.get("label", "no description provided"),  # could also have label from workflow.cwl, which might be more informative
        "end_time": stage.end_time.isoformat(),
        "environment": env,
        "input": sorted(inputs, key=lambda item: item.get("file_name", None)),
        "launch_config": {
            "arguments": args,
            "environment_variables": None,
            "executable": "python"   # todo: it won't always be python - from baseCommand in cwl files?
        },
        "output": sorted(outputs, key=lambda item: item.get("file_name", None)),
        "recipe_id": uuid_from_uri(plan_implementation.get("https://schema.org/identifier", None)),
        "resource_usage": [{
            "value": (stage.end_time - stage.start_time).total_seconds(),
            "units": "second"
        }],
        "start_time": stage.start_time.isoformat(),
        "status": "completed",
        # how to detect if there was an error in the CWL run?
        # I think it only generates the prov directory if it was successful
        "tags": ["cwl"],
        "type": guess_computation_type(stage.label, plan_implementation),  # could also use stage.intent
    }


def get_workflow_step(workflow_prospective, step_id):
    for workflow_step in workflow_prospective["steps"]:
        if workflow_step["id"] == step_id:
            return workflow_step
    return None


def upload_to_kg(filename, space):
    token = os.environ["EBRAINS_AUTH_TOKEN"]
    auth = {
        "Authorization": f"Bearer {token}"
    }
    url = f"https://prov-api.apps.tc.humanbrainproject.eu/workflows/?space={space}"

    with open(filename) as fp:
        data = json.load(fp)

    response = requests.post(url, json=data, headers=auth)
    if response.status_code == 201:
        print(f"Success. Workflow execution created with id {response.json()['id']}")
    else:
        print(f"Upload failed: {response.text}")


# We load the following data from the CWL provenance record:
#   - primary provenance document in JSON-LD format (as an rdflib RDF document)
#   - workflow job parameters (as JSON)
#   - workflow packed CWL file (as JSON)
def main(prov_dir, container_engine, upload_workspace):

    g = Graph()
    g.parse(f"{prov_dir}/metadata/provenance/primary.cwlprov.jsonld")

    with open(f"{prov_dir}/workflow/primary-job.json") as fp:
        job_config = json.load(fp)

    if "token" in job_config:
        job_config["token"] = "<MASKED SECRET>"

    with open(f"{prov_dir}/workflow/packed.cwl") as fp:
        packed_workflow = json.load(fp)

    workflow_stages_retrospective = g.subjects(RDF.type, URIRef("http://purl.org/wf4ever/wfprov#ProcessRun"))
    wf_engine = list(g.subjects(RDF.type, URIRef("http://purl.org/wf4ever/wfprov#WorkflowEngine")))[0]

    # the following is fine for simple workflows, will need to be rewritten for nested workflows
    if "$graph" in packed_workflow:
        workflow_prospective = [item for item in packed_workflow["$graph"]
                                if item["class"] == "Workflow"][0]
        workflow_stages_prospective = {item["id"]: item for item in packed_workflow["$graph"]
                                    if item["class"] == "CommandLineTool"}
        #workflow_stages_prospective = [workflow_stages_prospective[step["run"]]
        #                              for step in workflow_prospective["steps"]]
    else:
        assert packed_workflow["class"] == "CommandLineTool"
        workflow_prospective = []
        workflow_stages_prospective = {packed_workflow["id"]: packed_workflow}

    #breakpoint()
    prov_report = {
        "configuration": job_config,
        "recipe_id": uuid_from_uri(
            workflow_prospective.get("https://schema.org/identifier", None)
        ),
        "stages": []
    }

    for stage_node in workflow_stages_retrospective:

        stage = Stage(stage_node, g, prov_dir)
        workflow_step = get_workflow_step(workflow_prospective, stage.plan_id)
        workflow_step_implementation_id = workflow_step["run"]
        plan = workflow_stages_prospective[workflow_step_implementation_id]

        prov_for_stage = get_prov_for_stage(stage, workflow_step, plan, container_engine)
        prov_report["stages"].append(prov_for_stage)

    add_file_locations(prov_report["stages"], prov_dir)
    prov_report["stages"] = sorted(prov_report["stages"], key=lambda s: s["start_time"])


    output_file = os.path.join(prov_dir, "ebrains_prov_generated.json")
    with open(output_file, "w") as fp:
        json.dump(prov_report, fp, indent=2)
        fp.write("\n")

    if upload_workspace:
        upload_to_kg(output_file, upload_workspace)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="convert_cwlprov_to_ebrains.py",
        description="Upload workflow provenance metadata to EBRAINS",
    )
    parser.add_argument("--container-engine", default=DEFAULT_CONTAINER_ENGINE)
    parser.add_argument("--upload", default=None)
    parser.add_argument("prov_dir")

    args = parser.parse_args()
    main(args.prov_dir, args.container_engine, args.upload)
