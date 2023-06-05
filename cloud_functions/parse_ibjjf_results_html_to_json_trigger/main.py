import os
import json
from typing import List, Dict
from google.cloud import storage
from bs4 import BeautifulSoup


def get_soup_from_blob(html_blob):
    """
    converts an html file stored in the cloud
    to beautifulsoup object
    """
    blob_string = html_blob.download_as_text()
    soup = BeautifulSoup(blob_string, "html.parser")
    return soup


def extract_place_from_athlete(athlete):
    """ """
    place = athlete.find("div", attrs={"class": "position-athlete"})
    return place.text.strip()


def split(name_team):
    return name_team.strip().split("\n")


def get_athlete_name(name_team):
    return split(name_team)[0]


def get_athlete_team(name_team):
    return split(name_team)[-1].lstrip()


def extract_name_team_from_athlete(athlete):
    """
    extracts a combination of the athletes name and
    the team/gym/academy the athlete
    was representing at the tournament.
    """
    name = athlete.find("div", attrs={"class": "name"})
    name_team = name.find("p").text
    return get_athlete_name(name_team), get_athlete_team(name_team)


def parse_ibjjf_results_html_to_json_trigger(event, _):
    # bucket = storage_client.bucket(bucket_name)

    # dest_bucket_name = os.environ["BUCKET_NAME"]
    # dest_bucket = storage_client.bucket(dest_bucket_name)

    bucket_name = event["bucket"]  # bucket that triggers
    file_name = event["name"]  # new files will land in the bucket.
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    rows = []
    blob = bucket.blob(file_name)
    file_name = blob.name
    soup = get_soup_from_blob(blob)

    # two types of documents in document collection
    athletes_section = soup.find("div", attrs={"class": "col-sm-12 athletes"})
    athletes_section_type_two = soup.find(
        "div", attrs={"class": "col-xs-12 col-md-6 col-athlete"}
    )
    if athletes_section:
        division = athletes_section.find_all(
            "div", attrs={"class": "category mt-4 mb-3"}
        )

        for div in division:
            table = div.findNext("table")
            place = table.find_all("td", attrs={"class": "place"})
            athlete_academy = table.find_all(
                "td", attrs={"class": "athlete-academy"}
            )

            # athlete_name = table.find_all(
            #    'div', attrs={'class': 'athlete-name'})
            academy_name = [
                aa.find("div", attrs={"class": "academy-name"})
                for aa in athlete_academy
            ]
            athlete_name = [
                aa.find("div", attrs={"class": "athlete-name"})
                for aa in athlete_academy
            ]

            athlete_places = [pl.text for pl in place]
            athlete_name = [an.text for an in athlete_name]
            academy_name = [an.text for an in academy_name]
            for ap, at, ac in zip(athlete_places, athlete_name, academy_name):
                row = {}
                row["place"] = ap
                row["athlete"] = at
                row["academy"] = ac
                row["file_path"] = str(blob.name)
                row["division"] = div.text
                rows.append(row)

    elif athletes_section_type_two:
        category = athletes_section_type_two.find_all(
            "h4", attrs={"class": "subtitle"}
        )
        for cat in category:
            cat_list = cat.findNext("div")
            athletes = cat_list.find_all(
                "div", attrs={"class": "athlete-item"}
            )
            athlete_places = []
            athlete_academies = []
            athlete_names = []

            for athlete in athletes:
                place = extract_place_from_athlete(athlete)
                athlete_name, team_name = extract_name_team_from_athlete(
                    athlete
                )

                athlete_places.append(place)
                athlete_names.append(athlete_name)
                athlete_academies.append(team_name)

            for ap, at, ac in zip(
                athlete_places, athlete_names, athlete_academies
            ):
                row = {}
                row["place"] = ap
                row["athlete"] = at
                row["academy"] = ac
                row["file_path"] = str(blob.name)
                row["division"] = cat.text.strip()
                rows.append(row)

    else:
        pass

    write_to_bucket_name = os.environ["BUCKET_NAME"]
    write_to_bucket = storage_client.bucket(
        write_to_bucket_name
    )
    write_to_bucket.blob(
        file_name.replace(".html", "") + ".json"
    ).upload_from_string(data=json.dumps(rows))


if __name__ == "__main__":
    main()
