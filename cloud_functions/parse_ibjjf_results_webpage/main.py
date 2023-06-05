import os
import io
import csv
from typing import List, Dict
from google.cloud import storage
from bs4 import BeautifulSoup

def get_event_content(storage_client, bucket_name, file_name)-> bytes:
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    file_content = blob.download_as_bytes()
    return file_content

def parse_soup(soup) -> List[Dict[str, str]]:
    """
    parses the soup for event year and link to the event
    """
    data = []
    for a_el in soup.find_all("a", attrs={"class": "event-year-result"}):
        year = a_el["data-y"]
        event = a_el["data-n"]
        link = a_el["href"]

        data_dict = {}
        data_dict["year"] = year
        data_dict["event"] = event
        data_dict["link"] = link
        data.append(data_dict)
    return data

def write_data_to_stream(data: List[Dict[str, str]])-> str:
    """
    uses csv DictWriter to write list of dicts to
    text stream in csv format
    """
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["year", "event", "link"])
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()

def parse_ibjjf_results_webpage(event, context):
    """
    main function / entry point
    """
    bucket_name = event["bucket"]
    file_name = event["name"]
    storage_client = storage.Client()
    file_content = get_event_content(storage_client, bucket_name, file_name)

    soup = BeautifulSoup(file_content)
    data = parse_soup(soup)
    output = write_data_to_stream(data)

    write_to_bucket_name = os.environ["BUCKET_NAME"]
    write_to_bucket = storage_client.bucket(write_to_bucket_name)
    write_to_bucket.blob(
        file_name.replace("html", "") + ".csv"
    ).upload_from_string(output)
