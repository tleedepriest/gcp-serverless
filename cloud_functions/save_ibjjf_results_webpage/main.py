import os
import datetime
import requests
from google.cloud import storage

def get_output_filename():
    today = datetime.date.today()
    filename = f'{today}_ibjjf_results.html'
    return filename

def get_url(request):
    request_json = request.get_json()
    url = request_json['url']
    return url

def get_html_content(url):
    response = requests.get(url)
    html = response.text
    return html

def save_ibjjf_results_webpage(request):
    """
    main entry point. Cloud function triggered
    by HTTP request. Send function url of
    webpage we want to save.
    """
    url = get_url(request)
    html_content = get_html_content(url)
    filename = get_output_filename()

    bucket_name = os.environ["BUCKET_NAME"]

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(html_content)

    return 'Webpage saved to Cloud Storage'
