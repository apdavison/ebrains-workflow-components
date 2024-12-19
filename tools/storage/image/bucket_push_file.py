#!/usr/bin/env python3

import argparse
import hashlib
import json
import mimetypes
from pathlib import Path
import requests


def get_checksum(file_path):
    with open(file_path, "rb") as fp:
        return hashlib.sha1(fp.read()).hexdigest()


# function that pushes an object to a Collab bucket
def bucket_push_file(bucket_id, target_folder, token, *files):
    # get an upload url
    DATA_PROXY_ENDPOINT = 'https://data-proxy.ebrains.eu/api/v1/buckets'
    AUTHORIZATION_HEADERS = {'Authorization': f'Bearer {token}'}
    target_folder = target_folder.strip("/")
    remote_files = []
    errors = {}
    for file in files:
        basename = Path(file).name
        remote_url = f"{DATA_PROXY_ENDPOINT}/{bucket_id}/{target_folder}/{basename}"
        r_url = requests.put(remote_url, headers=AUTHORIZATION_HEADERS)   # temp url
        if r_url.status_code != 200:
            errors[file] = r_url.content
        upload_url = r_url.json()['url']
        response = requests.put(upload_url, data=open(file, 'rb').read())
        if response.status_code in (200, 201):
            remote_files.append({
                "location": remote_url,
                "basename": basename,
                "checksum": f"sha1${get_checksum(file)}",
                "size": Path(file).stat().st_size,
                "format": mimetypes.guess_type(file, strict=False)[0]
            })
        else:
            errors[file] = response.content
    if errors:
        raise Exception(str(errors))
    return remote_files


parser = argparse.ArgumentParser()
parser.add_argument('bucket_id', help='bucket where the file will be uploaded')
parser.add_argument('target_folder', help='path to folder within bucket')
parser.add_argument('token', help='token for access to the data-proxy')
parser.add_argument('files', help='files to be uploaded', nargs='+')
args = parser.parse_args()

# push files to bucket
response = bucket_push_file(args.bucket_id, args.target_folder, args.token, *args.files)

with open("cwl.output.json", "w") as fp:
    json.dump({"remote_files": response}, fp, indent=2)
    fp.write("\n")
