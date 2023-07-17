from typing import List

from models.flight_data import Focus


def postprocessing(batch_results, excludes: List[str]) -> List[Focus]:
    focuses: List[Focus] = []
    for text, ent_list in batch_results:
        ent_loc = set()
        ent_begin = set()
        for ent in ent_list:
            ent_type = ent["type"]
            if ent_type in excludes:
                continue
            start, end = ent["start_index"], ent["end_index"]
            ent_loc = ent_loc.union(set(range(start, end)))
            ent_begin.add(start)
        token = []
        flag = True
        span = set()
        for i, char in enumerate(text):
            if not char.isspace():
                token.append(char)
                flag &= (i in ent_loc)
                span.add(i)
                continue
            has_begin = len(span.intersection(ent_begin)) != 0
            focus = Focus(elem="".join(token),
                            flag=flag,
                            begin=has_begin)
            focuses.append(focus)
            token = []
            flag = True
            span = set()
        if len(token) != 0:
            has_begin = len(span.intersection(ent_begin)) != 0
            focus = Focus(elem="".join(token),
                            flag=flag,
                            begin=has_begin)
            focuses.append(focus)
    return focuses