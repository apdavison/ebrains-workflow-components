#!/usr/bin/env python3

import argparse
from pathlib import Path
import requests


# function that pushes an object to a Collab bucket
def bucket_push_file(bucket_id, target_folder, token, *files):
    # get an upload url
    DATA_PROXY_ENDPOINT = 'https://data-proxy.ebrains.eu/api/v1/buckets'
    AUTHORIZATION_HEADERS = {'Authorization': f'Bearer {token}'}
    target_folder = target_folder.strip("/")
    for file in files:
        basename = Path(file).name
        r_url = requests.put(f"{DATA_PROXY_ENDPOINT}/{bucket_id}/{target_folder}/{basename}", headers=AUTHORIZATION_HEADERS)   # temp url
        url = r_url.json()['url']
        # print bucket stats before upload
        response = requests.put(url, data=open(file, 'rb').read())


parser = argparse.ArgumentParser()
parser.add_argument('bucket_id', help='bucket where the file will be uploaded')
parser.add_argument('target_folder', help='path to folder within bucket')
parser.add_argument('token', help='token for access to the data-proxy')
parser.add_argument('files', help='files to be uploaded', nargs='+')
args = parser.parse_args()

# push files to bucket
bucket_push_file(args.bucket_id, args.target_folder, args.token, *args.files)
