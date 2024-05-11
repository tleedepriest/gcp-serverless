import re
import os
import csv
import requests
#from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from google.cloud import storage


def download_file(link, dest_blob):
    """
    returns html content (text) or None in case of error
    """
    try:
        response = requests.get(link)
        response.raise_for_status()
        html_content = response.text
    except requests.exceptions.HTTPError as e:
        return e.response.text

    dest_blob.upload_from_string(html_content)

def read_file_get_timestamp(dest_blob):
    blob_string = dest_blob.download_as_text()
    soup = BeautifulSoup(blob_string, "html.parser")
    timestamp = soup.find("small", {"class": "status"})
    if timestamp is not None:
        timestamp = timestamp.find("span").text
        if "Partial result" in timestamp:
            timestamp = re.split(r'\s+', timestamp)
            try:
                timestamp = '_'.join(timestamp[3:5]).replace(":", "").replace("/", "")
                return blob_string, timestamp
            except IndexError as e:
                print(f"{e} caused by {timestamp}")
                return blob_string, timestamp
    return blob_string, None


def get_all_ibjjf_results_webpages(event, context):
    bucket_name = event["bucket"]  # bucket that triggers
    file_name = event["name"]  # file that triggered
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    tmp_dest = f"/tmp/{file_name}"
    blob.download_to_filename(tmp_dest)
    # year, event, link
    dest_bucket_name = os.environ["BUCKET_NAME"]
    dest_bucket = storage_client.bucket(dest_bucket_name)

    with open(tmp_dest, "r") as fh:
        csv_file = csv.DictReader(fh)
        #with ThreadPoolExecutor(max_workers=20) as executor:
        for line in csv_file:
            link, event, year = line["link"], line["event"].replace(" ", "_"), line["year"]
            dest_blob_name = f"{event}_{year}.html"
            dest_blob = dest_bucket.blob(dest_blob_name)
            if int(float(year)) <= 2022:
                pass
            else:
                if not dest_blob.exists():
                    print(f"....downloading from {link}")
                    download_file(link, dest_blob)
            # only want to check any new files, so this value should be updated yearly...
            # need to parse new files in case they post a partial result
            # while running the pipeline.
            #elif int(float(year)) >= 2023 and dest_blob.exists():
            #    blob_string, timestamp = read_file_get_timestamp(dest_blob)
            #    if timestamp is not None:
            #        dest_blob_name = f'{dest_blob_name.replace(".html", "")}_{timestamp}.html'
            #        dest_blob = dest_bucket.blob(dest_blob_name)
            #        if not dest_blob.exists():
            #            dest_blob.upload_from_string(data=blob_string)
            #        else:
            #            print(f"The file already exists")


    os.remove(tmp_dest)
