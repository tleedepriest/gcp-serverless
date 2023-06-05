import io
import json
import re
import csv
import lxml
import cchardet
from typing import List, Dict
# from pathlib import Path
# import pandas as pd
from google.cloud import storage
#from collections import defaultdict
from bs4 import BeautifulSoup
#from html.parser import HTMLParser

# class MyHTMLParser(HTMLParser):
#     def __init__(self):
#         super().__init__()
#         self.div_attrs = []

#     def handle_starttag(self, tag, attrs):
#         for attr in attrs:
#             attr = '|'.join(attr)
#             if attr not in self.div_attrs and "div" in tag:
#                 self.div_attrs.append(attr)

#     def handle_endtag(self, tag):
#         pass
#         #print("Encountered an end tag :", tag)

#     def handle_data(self, data):
#         pass
#         #print("Encountered some data  :", data)

# def get_soup_from_static_html(html):
#     """
#     Parameters
#     ----------------
#     html: str/path obj
#         the path to the html file

#     Returns
#     -----------------
#     soup: bs4 Soup obj
#     """
#     with open(html, "r") as fh:
#         soup = BeautifulSoup(fh, "lxml")
#         # contents = fh.read()
#         # soup = BeautifulSoup(contents, features='lxml')
#     return soup

def get_soup_from_blob(html_blob):
    blob_string = html_blob.download_as_text()
    soup = BeautifulSoup(blob_string, "lxml")
    return soup


# def janky_text_strip(soup):
#     """
#     has major issues, like replacing text within attributes,
#     does seem to preserve most html though!
#     """

#     with open(html, "r") as fh:
#         html_string = fh.read()
#     only_text = soup.text
#     tokens = re.split('\s+', only_text)
#     tokens = list(set(tokens))
#     for tok in tokens:
#          html_string = html_string.replace(tok, '')
#     print(html_string)

# def get_file_list(path_to_dir):
#     """
#     return all files in a given directory
#     """
#     return [x for x in Path(path_to_dir).glob("**/*") if x.is_file()]

def list_blobs(storage_client, bucket_name):
    """Lists all the blobs in the bucket."""
    # bucket_name = "your-bucket-name"

    storage_client = storage.Client()

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(bucket_name)
    return blobs
    # Note: The call returns a response only when the iterator is consumed.
    #for blob in blobs:
    #    print(blob.name)

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


def main(
        #event, context
        ):
    #bucket = storage_client.bucket(bucket_name)
    #blob = bucket.blob(file_name)
    #tmp_dest = f"/tmp/{file_name}"
    #file_content = blob.download_to_filename(tmp_dest)
    #dest_bucket_name = os.environ["BUCKET_NAME"]
    #dest_bucket = storage_client.bucket(dest_bucket_name)
    
    #htmls = get_file_list(
    #    "/media/sf_VM_shared/bjj_lineage/generated_data/ibjjf/events/"
    #)
    #bucket_name = event["bucket"]  # bucket that triggers
    #file_name = event["name"]  # new files will land in the bucket.
    bucket_name = "bjj-lineage-ibjjf-events-results-all"
    storage_client = storage.Client()
    #rows = []
    html_blobs = list_blobs(storage_client, bucket_name)
    
    for num, blob in enumerate(html_blobs):
        
        file_name = blob.name
        soup = get_soup_from_blob(blob)

        #with open(html, "r") as fh:
        #    html_string = fh.read()
        #parser = MyHTMLParser()
        #parser.feed(html_string)
        #file_signature = parser.div_attrs

        rows = []
        file_name = blob.name
        #division_results = defaultdict(list)
        soup = get_soup_from_blob(blob)

        #with open(html, "r") as fh:
        #    html_string = fh.read()
        #parser = MyHTMLParser()
        #parser.feed(html_string)
        #file_signature = parser.div_attrs
        #timestamp = soup.find("small", {"class": "status"})
        #if timestamp is not None:
        #    timestamp_text = timestamp.find("span").text
        #    if "Partial result" in timestamp_text:
        #        print(file_name)
        #        print(timestamp)
        #    else:
        #        print(num)
        #if timestamp is not None:
        #    
        athletes_section = soup.find(
            "div", attrs={"class": "col-sm-12 athletes"}
        )
        athletes_section_type_two = soup.find(
            "div", attrs={"class": "col-xs-12 col-md-6 col-athlete"}
        )

        if athletes_section:
            division = athletes_section.find_all(
                "div", attrs={"class": "category mt-4 mb-3"}
            )

            for div in division:
                table = div.findNext('table')
                place = table.find_all('td', attrs={'class': 'place'})
                athlete_academy = table.find_all(
                    'td', attrs={'class': 'athlete-academy'})

                #athlete_name = table.find_all(
                #    'div', attrs={'class': 'athlete-name'})
                academy_name = [aa.find('div', attrs={'class': 'academy-name'}) for aa in athlete_academy]
                athlete_name = [aa.find('div', attrs={'class': 'athlete-name'}) for aa in athlete_academy]

                athlete_places = [
                    pl.text for pl
                    in place]
                athlete_name = [
                    an.text for an
                    in athlete_name]
                academy_name = [
                    an.text for an
                    in academy_name]
                for ap, at, ac in zip(athlete_places, athlete_name, academy_name):
                    row = {}
                    row["place"] = ap
                    row["athlete"] = at
                    row["academy"] = ac
                    row["file_path"] = str(blob.name)
                    row["division"] = div.text
                    rows.append(row)

                #division_results["place"].extend(athlete_places)
                #division_results["athlete"].extend(athlete_name)
                #division_results["academy"].extend(academy_name)

                #division_results["file_path"].extend(
                #    [str(html)]*len(place))
                #division_results["division"].extend(
                #    [div.text]*len(place))

        elif athletes_section_type_two:
            category = athletes_section_type_two.find_all("h4", attrs={"class": "subtitle"})
            for cat in category:

                cat_list = cat.findNext("div")
                athletes = cat_list.find_all("div", attrs={"class": "athlete-item"})
                athlete_places = []
                athlete_academies = []
                athlete_names = []

                for athlete in athletes:
                    place = athlete.find(
                        "div", attrs={"class": "position-athlete"}
                    )
                    athlete_places.append(place.text.strip())
                    name = athlete.find("div", attrs={"class": "name"})
                    name_team = name.find("p").text
                    name_team_split = name_team.strip().split("\n")
                    athlete_name = name_team_split[0]
                    team_name = name_team_split[-1].lstrip()
                    athlete_academies.append(team_name)
                    athlete_names.append(athlete_name)

                #num_contenders = len(athlete_places)

                for ap, at, ac in zip(athlete_places, athlete_names, athlete_academies):
                    row = {}
                    row["place"] = ap
                    row["athlete"] = at
                    row["academy"] = ac
                    row["file_path"] = str(blob.name)
                    row["division"] = cat.text.strip()
                    rows.append(row)

                #division_results["timestamp"].extend([timestamp]* num_contenders)
                # division_results["file_path"].extend([str(html)] * num_contenders)
                # division_results["division"].extend(
                #         [cat.text.strip()] * num_contenders
                #     )
                # division_results["place"].extend(athlete_places)
                # division_results["athlete"].extend(athlete_names)
                # division_results["academy"].extend(athlete_academies)

        else:
            pass

    write_to_bucket = storage_client.bucket("bjj-lineage-ibjjf-events-results-all-parsed-json")
    write_to_bucket.blob(
        file_name.replace(".html", "") + ".json"
    ).upload_from_string(data=json.dumps(rows))

        #try:
        #    df = pd.DataFrame.from_dict(division_results)
        #    successful_dfs.append(df)
        #except ValueError:
        #    print(html)
        #    print(athletes_section_type_two)
        #    print(division_results)

    #with open('test.csv', 'w') as csvfile:
    #    writer = csv.DictWriter(csvfile, fieldnames=['place', 'athlete', 'academy', 'file_path', 'division'])
    #    writer.writeheader()
    #    writer.writerows(rows)
    # with open("file_signatures.txt", "w") as fh:
    #     for key, value in file_signatures.items():
    #         fh.write(f"{key}:\n\n")
    #         for file in value:
    #             fh.write(f"{file}\n")
    #final = pd.concat(successful_dfs)
    #final.to_csv("test.csv", index=False)

if __name__ == "__main__":
    main()
