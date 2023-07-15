import os
import requests
from typing import List

from models.flight_data import Focus

AMAP_API_KEY = os.environ.get("AMAP_API_KEY", None)
MAJORITY_SCORE_THRESHOLD = 3
ABOVE_AVG_MAXIMUM_CITIES = 3

def estimate_scope(loc_list: List[str]) -> List[str]:
    endpoint = "https://restapi.amap.com/v5/geocode/geo"
    params = {"key": AMAP_API_KEY}
    scores = {}
    for loc in loc_list:
        loc = loc.replace(" ", "")
        params["address"] = loc
        response = None
        try:
            response = requests.get(endpoint, params)
        except Exception as e:
            raise e
        if response is None or response["status"] == "0":
            continue
        geo_data = response["geocodes"][0]
        scope_level, city = geo_data["level"], geo_data["city"]
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
    median = scores_sum[-1] // 2
    if scores_sum[0] >= median:
        return [scores[0][0]]
    return [x[0] for x in scores if x[1] > scores_avg][:ABOVE_AVG_MAXIMUM_CITIES]

def fetch_location(focuses: List[Focus], scope: List[str]):
    endpoint = "https://restapi.amap.com/v3/place/text"
    params = {"key": AMAP_API_KEY}