import os
import requests
import concurrent.futures
from typing import List

from models.flight_data import Focus

AMAP_API_KEY = os.environ.get("AMAP_API_KEY", None)
MAJORITY_SCORE_THRESHOLD = 3
ABOVE_AVG_MAXIMUM_CITIES = 3

def estimate_scope(loc_list: List[str]) -> List[str]:
    endpoint = "https://restapi.amap.com/v5/geocode/geo"
    est_params = []
    scores = {}
    for loc in loc_list:
        loc = loc.replace(" ", "")
        est_params.append(loc)
    est_results = None
    with concurrent.futures.ThreadPoolExecutor() as estimator:
        est_results = estimator.map(lambda x: _estimate_scope(x), est_params)
    # if est_results is not None:
    #     est_results = list(est_results)
    for scope_level, city in est_results:
        if isinstance(city, list) and len(city) == 0:
            continue
        curr_city_score = scores.get(city, 0)
        if scope_level in {"省", "市", "区县", "开发区", "乡镇"}:
            scores.update({city: curr_city_score + 3})
        elif scope_level in {"村庄", "热点商圈", "兴趣点", "道路"}:
            scores.update({city: curr_city_score + 1})
    scores = sorted(filter(lambda x: x[1] >= MAJORITY_SCORE_THRESHOLD, scores.items()), key=lambda x: x[1], reverse=True)
    if len(scores) == 0:
        return []
    scores_sum = sum([x[1] for x in scores])
    scores_avg = scores_sum / len(scores)
    median = scores_sum // 2
    if scores[0][1] >= median:
        return [scores[0][0]]
    return [x[0] for x in scores if x[1] > scores_avg][:ABOVE_AVG_MAXIMUM_CITIES]

def fetch_location(focuses: List[Focus], scopes: List[str]):
    endpoint = "https://restapi.amap.com/v3/place/text"
    params = {"key": AMAP_API_KEY}
    begins = [i for i, focus in enumerate(focuses) if focus.begin]
    fragments = [focuses[i:j] for i, j in zip(begins, begins[1:] + [len(focuses)])]
    fragments = [list(filter(lambda focus: focus.flag, fragment)) for fragment in fragments]
    entities = {"".join([focus.elem for focus in fragment]): fragment for fragment in fragments}
    est_params = [(name, city) for name in entities.keys() for city in scopes]
    est_results = None
    with concurrent.futures.ThreadPoolExecutor() as estimator:
        est_results = estimator.map(lambda x: _estimate_location(*x), est_params)
    if est_results is not None:
        est_results = list(est_results)
    print(est_results)

def _estimate_location(query: str, scope: str):
    endpoint = "https://restapi.amap.com/v3/assistant/inputtips"
    params = {"key": AMAP_API_KEY,
              "keywords": query,
              "city": scope,
              "citylimit": True}
    response = None
    try:
        response = requests.get(endpoint, params).json()
    except Exception as e:
        raise e
    return response["tips"] if response is not None and response["status"] == "1" else []

def _estimate_scope(address: str):
    endpoint = "https://restapi.amap.com/v5/geocode/geo"
    params = {"key": AMAP_API_KEY,
              "address": address}
    response = None
    try:
        response = requests.get(endpoint, params).json()
    except Exception as e:
        raise e
    return response["geocodes"][0]["level"], response["geocodes"][0]["city"] if response is not None and response["status"] == "1" else None