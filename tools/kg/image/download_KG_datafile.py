#!/usr/bin/env python
"""
This script downloads the data for a dataset identified by an EBRAINS KnowledgeGraph UUID
to a local directory.

By running this script, you agree to accept the EBRAINS terms of use.

Author: Andrew Davison, CNRS
Year: 2023
"""

import os
import json
from pathlib import Path
import zipfile
import requests
import click

from fairgraph import KGClient
from fairgraph.openminds.core import DatasetVersion


@click.command()
@click.argument("uuid")
@click.argument("file_path")
@click.option("--token", default=None, help="An EBRAINS OIDC Bearer token")
@click.option(
    "-d",
    "--download-dir",
    default="downloads",
    help="The directory into which data will be downloaded.",
)
def main(uuid, file_path, token, download_dir):
    client = KGClient(token=token, host="core.kg.ebrains.eu")
    dataset_version = DatasetVersion.from_id(uuid, client, scope="any", follow_links={"repository": {"files": {}}})
    for file_ in dataset_version.repository.files:
        if file_path in str(file_.iri):
            file_.download(Path(download_dir) / Path(file_path), client, accept_terms_of_use=True)
            break

    # archive_path, repository_uri = dataset_version.download(
    #     download_dir, client, accept_terms_of_use=True
    # )
    # resolved_repo_uri = repository_uri.replace("?prefix=", "/")

    # with zipfile.ZipFile(archive_path, "r") as archive:
    #     archive.extractall(path=os.path.dirname(archive_path))
    #     file_paths = archive.namelist()
    # os.remove(archive_path)
    # with open(os.path.join(download_dir, "kg_download_manifest.json"), "w") as fp:
    #     json.dump(
    #         {file_path: f"{resolved_repo_uri}/{file_path}" for file_path in file_paths},
    #         fp,
    #         indent=2,
    #     )
    # # todo: add error handling


if __name__ == "__main__":
    main()
