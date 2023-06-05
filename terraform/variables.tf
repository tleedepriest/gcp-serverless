locals {
  ibjjf_bucket = "ibjjf_data_lake"
}

variable "project" {
  default     = "bjj-lineage-383401"
  description = "The project id"
}


variable "region" {
  description = "Region for GCP resources. Choose as per your location: https://cloud.google.com/about/locations"
  default     = "us-east4"
  type        = string
}

variable "zone" {
  description = ""
  default     = "us-east4-b"
  type        = string
}

variable "credentials" {
  description = "path to credentials file rather than setting env var."
  default     = "~/.google/credentials/gcs_credentials_bjj_lineage.json"
  type        = string
}

variable "storage_class" {
  description = "Storage class type for your bucket. Check official docs for more info."
  default     = "STANDARD"
}
