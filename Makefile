save_dir = cloud_functions/save_ibjjf_results_webpage
parse_dir = cloud_functions/parse_ibjjf_results_webpage
get_dir = cloud_functions/get_all_ibjjf_results_webpages

.PHONY: zip_all
.PHONY: deploy
zip_all:
	cd $(save_dir); zip -FSr save-ibjjf-results-webpage.zip main.py requirements.txt
	cd $(parse_dir); zip -FSr parse-ibjjf-results-webpage.zip main.py requirements.txt
	cd $(get_dir); zip -FSr get-all-ibjjf-results-webpages.zip main.py requirements.txt

deploy: zip_all
	cd terraform; terraform apply

