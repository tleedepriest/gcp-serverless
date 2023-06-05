terraform {
  required_version = ">= 1.0"
  backend "local" {} # Can change from "local" to "gcs" (for google) or "s3" (for aws), if you would like to preserve your tf-state online
  required_providers {
    google = {
      source = "hashicorp/google"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "3.1.0"
    }
  }
}

provider "google" {
  project     = var.project
  region      = var.region
  credentials = file(var.credentials) # Use this if you do not want to set env-var GOOGLE_APPLICATION_CREDENTIALS
}

data "google_storage_project_service_account" "gcs_account" {
}

resource "random_id" "bucket_prefix" {
  byte_length = 8
}

resource "random_id" "bucket2_prefix" {
  byte_length = 8
}

resource "google_storage_bucket" "bucket" {
  name                        = "${random_id.bucket_prefix.hex}-gcf-source" # Every bucket name must be globally unique
  location                    = var.region
  uniform_bucket_level_access = true
}

# make request to get latest version of ibjjf webpage
resource "google_storage_bucket" "results_bucket" {
  name                        = "bjj-lineage-ibjjf-events-results"
  location                    = var.region
  uniform_bucket_level_access = true
}

# parse webpage to create csv of links with metadata
resource "google_storage_bucket" "parsed_results_bucket" {
  name                        = "bjj-lineage-ibjjf-events-results-parsed"
  location                    = var.region
  uniform_bucket_level_access = true
}

# request links from previous file and download html
resource "google_storage_bucket" "all_results_bucket" {
  name                        = "bjj-lineage-ibjjf-events-results-all"
  location                    = var.region
  uniform_bucket_level_access = true
}

# parse html pages to json - prepare for final aggregation
resource "google_storage_bucket" "all_results_json_bucket" {
  name                        = "bjj-lineage-ibjjf-events-results-all-parsed-json"
  location                    = var.region
  uniform_bucket_level_access = true
}

# where to store source code for execution of above steps
resource "google_storage_bucket_object" "object" {
  name   = "save-ibjjf-results-webpage.zip"
  bucket = google_storage_bucket.bucket.name
  source = "../cloud_functions/save_ibjjf_results_webpage/save-ibjjf-results-webpage.zip" 

}

resource "google_storage_bucket_object" "object2" {
  name   = "parse-ibjjf-results-webpage.zip"
  bucket = google_storage_bucket.bucket.name
  source = "../cloud_functions/parse_ibjjf_results_webpage/parse-ibjjf-results-webpage.zip"
}

resource "google_storage_bucket_object" "object3" {
  name   = "get-all-ibjjf-results-webpages.zip"
  bucket = google_storage_bucket.bucket.name
  source = "../cloud_functions/get_all_ibjjf_results_webpages/get-all-ibjjf-results-webpages.zip"
}

resource "google_storage_bucket_object" "object4" {
  name   = "parse-ibjjf-results-html-to-json-trigger.zip"
  bucket = google_storage_bucket.bucket.name
  source = "../cloud_functions/parse_ibjjf_results_html_to_json_trigger/parse-ibjjf-results-html-to-json-trigger.zip"
}

# configure the cloud functions architecure/environment for above steps
resource "google_cloudfunctions2_function" "function" {
  name        = "function-v2"
  location    = var.region
  description = "runs when http request is sent with url to save html of url sent"

  build_config {
    runtime     = "python38"
    entry_point = "save_ibjjf_results_webpage" # Set the entry point
    source {
      storage_source {
        bucket = google_storage_bucket.bucket.name
        object = google_storage_bucket_object.object.name
      }

    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "256M"
    timeout_seconds    = 60
    environment_variables = {
      BUCKET_NAME = google_storage_bucket.results_bucket.name
    }
  }
}

# To use GCS CloudEvent triggers, the GCS service account requires the Pub/Sub Publisher(roles/pubsub.publisher) IAM role in the specified project.
# (See https://cloud.google.com/eventarc/docs/run/quickstart-storage#before-you-begin)
resource "google_project_iam_member" "gcs-pubsub-publishing" {
  project = var.project
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"
}

resource "google_service_account" "account" {
  account_id   = "gcf-sa"
  display_name = "Test Service Account - used for both the cloud function and eventarc trigger in the test"
}

# Permissions on the service account used by the function and Eventarc trigger
resource "google_project_iam_member" "invoking" {
  project = var.project
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.account.email}"
  depends_on = [google_project_iam_member.gcs-pubsub-publishing]
}

resource "google_project_iam_member" "event-receiving" {
  project = var.project
  role    = "roles/eventarc.eventReceiver"
  member  = "serviceAccount:${google_service_account.account.email}"
  depends_on = [google_project_iam_member.invoking]
}

resource "google_project_iam_member" "artifactregistry-reader" {
  project = var.project
  role     = "roles/artifactregistry.reader"
  member   = "serviceAccount:${google_service_account.account.email}"
  depends_on = [google_project_iam_member.event-receiving]
}

resource "google_cloudfunctions2_function" "function2" {
  depends_on = [
    google_project_iam_member.event-receiving,
    google_project_iam_member.artifactregistry-reader,
  ]
  name        = "parse-ibjjf-results-webpage"
  location    = var.region
  description = "triggers on save of webpage in bucket. parses links/metadata from webpage into csv"

  build_config {
    runtime     = "python38"
    entry_point = "parse_ibjjf_results_webpage" # Set the entry point
    source {
      storage_source {
        bucket = google_storage_bucket.bucket.name
        object = google_storage_bucket_object.object2.name
      }

    }
  }

  event_trigger {
    event_type = "google.cloud.storage.object.v1.finalized"
    event_filters {
      attribute = "bucket"
      value = google_storage_bucket.results_bucket.name
    }
    retry_policy = "RETRY_POLICY_RETRY"
  }

  service_config {
    max_instance_count = 1
    available_memory   = "256M"
    environment_variables = {
      BUCKET_NAME = google_storage_bucket.parsed_results_bucket.name
    }
  }
}

resource "google_cloudfunctions2_function" "function3" {
  depends_on = [
    google_project_iam_member.event-receiving,
    google_project_iam_member.artifactregistry-reader,
  ]
  name        = "get-all-ibjjf-results-webpages"
  location    = var.region
  description = "reads csv and saves all links from file into bucket ~1200 files"

  build_config {
    runtime     = "python38"
    entry_point = "get_all_ibjjf_results_webpages" # Set the entry point
    source {
      storage_source {
        bucket = google_storage_bucket.bucket.name
        object = google_storage_bucket_object.object3.name
      }

    }
  }

  event_trigger {
    event_type = "google.cloud.storage.object.v1.finalized"
    event_filters {
      attribute = "bucket"
      value = google_storage_bucket.parsed_results_bucket.name
    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "256M"
    timeout_seconds    = 60
    environment_variables = {
      BUCKET_NAME = google_storage_bucket.all_results_bucket.name
    }
  }
}

resource "google_cloudfunctions2_function" "function4" {
  depends_on = [
    google_project_iam_member.event-receiving,
    google_project_iam_member.artifactregistry-reader,
  ]
  name        = "parse-ibjjf-results-html-to-json-trigger"
  location    = var.region
  description = "parses an html page that lands in the all_results_bucket to json"

  build_config {
    runtime     = "python38"
    entry_point = "parse_ibjjf_results_html_to_json_trigger" # Set the entry point
    source {
      storage_source {
        bucket = google_storage_bucket.bucket.name
        object = google_storage_bucket_object.object4.name
      }

    }
  }

  event_trigger {
    event_type = "google.cloud.storage.object.v1.finalized"
    event_filters {
      attribute = "bucket"
      value = google_storage_bucket.all_results_bucket.name
    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "256M"
    timeout_seconds    = 60
    environment_variables = {
      BUCKET_NAME = google_storage_bucket.all_results_json_bucket.name
    }
  }
}


output "function_uri" {
  value = google_cloudfunctions2_function.function.service_config[0].uri
}
