import os
import requests
import concurrent.futures
from typing import List, Optional, Tuple

from models.flight_data import Loc
from models.flight_data import FocusLoc
from models.flight_data import Focus

AMAP_API_KEY = os.environ.get("AMAP_API_KEY", "5170dc3bff37cf0e6a82b6440527eb20")
MAJORITY_SCORE_THRESHOLD = 3
ABOVE_AVG_MAXIMUM_CITIES = 1
MAXIMUM_HINT_COUNT = 3

def estimate_scope_and_anchors(loc_list: List[str], preset_scopes: List[str]) -> List[Tuple[str, str]]:
    candidate_cities = set([city for city in preset_scopes])
    has_preset = bool(preset_scopes)
    est_params = set()
    scores = {}
    for loc in loc_list:
        loc = loc.replace(" ", "")
        est_param = [(loc, candidate) for candidate in candidate_cities] if has_preset else [(loc, "")]
        est_params = est_params.union(est_param)
    est_results = None
    est_params = list(est_params)
    with concurrent.futures.ThreadPoolExecutor() as estimator:
        est_results = estimator.map(lambda x: _find_anchor(*x), est_params)
    pois = []
    anchors = []
    for raw, elem in zip(est_params, est_results):
        print(raw, elem)
        if elem is None:
            continue
        scope_level, city, location = elem["level"], elem["city"], elem["location"]
        curr_city_score = scores.get(city, 0)
        if scope_level in {"省", "市", "区县", "开发区", "乡镇"}:
            scores.update({city: curr_city_score + 3})
        elif scope_level in {"热点商圈", "兴趣点", "道路"}:
            pois.append((raw, city))
            scores.update({city: curr_city_score + 1})
        if preset_scopes:
            anchors.append((city, location))
    if preset_scopes:
        return anchors
    scores = sorted(filter(lambda x: x[1] >= MAJORITY_SCORE_THRESHOLD, scores.items()), key=lambda x: x[1], reverse=True)
    if len(scores) == 0:
        return []
    scores_sum = sum([x[1] for x in scores])
    scores_avg = scores_sum / len(scores)
    median = scores_sum // 2
    if scores[0][1] >= median:
        candidate_cities.add(scores[0][0])
    else:
        candidate_cities = candidate_cities.union([x[0] for x in scores if x[1] >= scores_avg][:ABOVE_AVG_MAXIMUM_CITIES])
    print(candidate_cities)
    remain_pois = ((raw[0], ct) for raw, _ in filter(lambda raw: raw[1] not in candidate_cities, pois) for ct in candidate_cities)
    with concurrent.futures.ThreadPoolExecutor() as estimator:
        est_results = estimator.map(lambda x: _find_anchor(*x), remain_pois)
    anchors = [(elem["city"], elem["location"]) for elem in est_results if elem is not None]
    return anchors
    

def fetch_location(focuses: List[Focus], anchors: List[Tuple[str, str]]):
    anchors = [""] if not anchors else anchors
    begins = [i for i, focus in enumerate(focuses) if focus.begin]
    # TODO
    # if len(begins) == 0
    fragments = [focuses[i:j] for i, j in zip(begins, begins[1:] + [len(focuses)])]
    fragments = [list(filter(lambda focus: focus.flag, fragment)) for fragment in fragments]
    entities = {"".join([focus.elem for focus in fragment]): fragment for fragment in fragments}
    est_params = [(name, anchor) for name in entities.keys() for anchor in anchors]
    est_results = None
    with concurrent.futures.ThreadPoolExecutor() as estimator:
        est_results = estimator.map(lambda x: _find_hint(*x), est_params)
    if est_results is not None:
        est_results = list([x[:MAXIMUM_HINT_COUNT] for x in est_results])
    for param, result in zip(est_params, est_results):
        key = param[0]
        sub_focuses = entities.get(key, [])
        locs = [Loc(location=elem["location"], name=elem["name"], id=elem["id"]) for elem in result if elem["id"]]
        focus_locs = [FocusLoc(**focus.dict(), loc=locs) for focus in sub_focuses]

def _find_hint(query: str, anchor: str | Tuple[str, str]):
    endpoint = "https://restapi.amap.com/v3/assistant/inputtips"
    params = {"key": AMAP_API_KEY,
              "keywords": query}
    if anchor:
        if isinstance(anchor, str):
            city = anchor
        city = anchor[0]
        location = anchor[1]
        params.update({"city": city,
                       "citylimit": True,
                       "location": location})
    response = None
    try:
        response = requests.get(endpoint, params).json()
    except Exception as e:
        raise e
    return response["tips"] \
    if response is not None and response["status"] == "1" else []

def _find_anchor(address: str, city: Optional[str] = None):
    endpoint = "https://restapi.amap.com/v3/geocode/geo"
    params = {"key": AMAP_API_KEY,
              "address": address}
    if city:
        params.update({"city": city})
    response = None
    print(params)
    try:
        response = requests.get(endpoint, params).json()
    except Exception as e:
        raise e
    return response["geocodes"][0] \
    if response is not None and response["status"] == "1" else None