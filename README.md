# gcp-serverless

## Purpose

Provide a third-party website/application to visualize and explore IBJJF Results
https://ibjjf.com/events/results

The current results are "locked" into inaccessible PDF formats.

## Pipeline details

A repository for a simple event-triggered pipeline. The steps below describe the basic pipeline.

1. The pipeline kicks off with a properly formatted http request to the initial cloud function. This request is read by a python function that saves a webpage to a bucket with a timestamp. 

2. The saved html page triggers a second function that parses the html page of all of the links. The links are saved as a CSV with metadata. 

3. The third trigger requests each HTML page corresponding to each link in the CSV file. All of these HTML pages are stored in a third bucket. The HTML pages are only requested if the file in the bucket doesn't already exist.

4. The HTML pages are parsed using beautiful soup into JSON format into a final bucket.

## Streamlit App
5. All of the json files are aggregated into a pandas dataframe, which is then deduplicated and read by the streamlit app. The streamlit app will read the files every __ time.




