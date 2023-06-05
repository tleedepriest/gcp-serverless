from unittest.mock import Mock
import pytest
import requests_mock
from cloud_functions.save_ibjjf_results_webpage.main import get_output_filename, get_url, get_html_content
from cloud_functions.parse_ibjjf_results_webpage.main import write_data_to_stream

def test_get_url():
    name = 'test'
    data = {'url': name}
    req = Mock(get_json=Mock(return_value=data), args=data)
    assert get_url(req) == "test"

@requests_mock.Mocker(kw='mock')
def test_get_html_content(**kwargs):
    test_url = "https://www.test.com"
    kwargs['mock'].get(test_url, text="html data")
    assert "html data" == get_html_content(test_url)

def test_write_data_to_stream():
    data = [{
        "event": "some_event",
        "year": "2022",
        "link": "some_link"}]
    output= "year,event,link\r\n2022,some_event,some_link\r\n"
    assert output == write_data_to_stream(data)
