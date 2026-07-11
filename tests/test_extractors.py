import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "extractors"))

import pytest
import responses

from extract_jobs import fetch_page, extract_all_jobs, BASE_URL


@responses.activate
def test_fetch_page_returns_results():
    responses.add(
        responses.GET,
        f"{BASE_URL}/1",
        json={"results": [{"id": "1", "title": "Data Engineer"}], "count": 1},
        status=200,
    )

    result = fetch_page(1)

    assert "results" in result
    assert len(result["results"]) == 1
    assert result["results"][0]["title"] == "Data Engineer"


@responses.activate
def test_fetch_page_handles_empty_results():
    responses.add(
        responses.GET,
        f"{BASE_URL}/1",
        json={"results": [], "count": 0},
        status=200,
    )

    result = fetch_page(1)

    assert result["results"] == []


@responses.activate
def test_extract_all_jobs_stops_on_empty_page():
    responses.add(
        responses.GET,
        f"{BASE_URL}/1",
        json={"results": [{"id": "1", "title": "Data Engineer"}], "count": 1},
        status=200,
    )
    responses.add(
        responses.GET,
        f"{BASE_URL}/2",
        json={"results": [], "count": 0},
        status=200,
    )

    jobs = extract_all_jobs()

    assert len(jobs) == 1
    assert jobs[0]["id"] == "1"


@responses.activate
def test_fetch_page_raises_on_server_error():
    responses.add(
        responses.GET,
        f"{BASE_URL}/1",
        json={"error": "server error"},
        status=500,
    )

    with pytest.raises(Exception):
        fetch_page(1)