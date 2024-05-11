top = cloud_functions
desc = ibjjf_results
save_dir = $(top)/save_$(desc)_webpage
parse_dir = $(top)/parse_$(desc)_webpage
get_dir = $(top)/get_all_$(desc)_webpages
parse_to_json_dir = $(top)/parse_$(desc)_html_to_json_trigger

.PHONY: zip_all
.PHONY: deploy
zip_all:
	cd $(save_dir); zip -FSr save-ibjjf-results-webpage.zip main.py requirements.txt
	cd $(parse_dir); zip -FSr parse-ibjjf-results-webpage.zip main.py requirements.txt
	cd $(get_dir); zip -FSr get-all-ibjjf-results-webpages.zip main.py requirements.txt
	cd $(parse_to_json_dir); zip -FSr parse-ibjjf-results-html-to-json-trigger.zip main.py requirements.txt
deploy: zip_all
	cd terraform; terraform apply

