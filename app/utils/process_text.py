import os
import json
import numpy as np
import onnxruntime as ort

from typing import List, Optional
from scipy.special import softmax
from paddlenlp.transformers import AutoTokenizer
from utils.locate import fetch_location

from utils.locate import estimate_scope_and_anchors
from models.flight_data import Focus
from models.utils import Entity

MAX_NUM_CHUNKS = 16
MIN_CHUNK_SIZE_CHARS = 10
CLOSED_EXTRACT_SEQ_LEN = 256 - 2

current_dir = os.path.dirname(os.path.abspath(__file__))
model_dir = os.path.join(current_dir, "../../static/models")

tokenizer = AutoTokenizer.from_pretrained(model_dir)

sess_options = ort.SessionOptions()
sess_options.intra_op_num_threads = 2
sess_options.inter_op_num_threads = 2
sess_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
predictor = ort.InferenceSession(os.path.join(model_dir, "inference.onnx"), 
                                 sess_options=sess_options, 
                                 providers=["CPUExecutionProvider"])

model_config_file = os.path.join(model_dir, "model_config.json")
with open(model_config_file, encoding="utf-8") as f:
    model_config = json.load(f)
label_maps = model_config["label_maps"]
# TODO
# task_type = model_config["task_type"]
# schema = model_config["label_maps"]["schema"]
# _set_schema(schema)

def extract_entry(text: str, closed: bool = False) -> List:
    if closed:
        entities = _closed_extract(text)
    else:
        entities = _opened_extract(text)
    return entities

def _closed_extract(text: str) -> List:
    chunks = _chunkify(text, CLOSED_EXTRACT_SEQ_LEN)
    tokenized_inputs = tokenizer(chunks,
                                 max_length=256,
                                 padding=False,
                                 truncation=True,
                                 return_attention_mask=True,
                                 return_offsets_mapping=True,
                                 return_token_type_ids=False)
    input_ids, attention_masks, offset_mappings = tokenized_inputs["input_ids"], tokenized_inputs["attention_mask"], tokenized_inputs["offset_mapping"]
    batch_outputs = []
    for i, (input_id, attention_mask) in enumerate(zip(input_ids, attention_masks)):
        input_dict = {"input_ids": np.array(input_id).astype("int64").reshape((1, -1)),
                      "att_mask": np.array(attention_mask).astype("int64").reshape((1, -1))}
        logits = predictor.run(None, input_dict)
        batch_outputs.extend(logits)
    decoded = _decode_batch(batch_outputs, offset_mappings, chunks)
    return decoded

def _opened_extract(text: str) -> List:
    # TODO
    pass

def _decode_batch(batch_outputs, offset_mappings, texts):
    batch_ent_results = []
    for entity_output, offset_mapping, text in zip(batch_outputs, offset_mappings, texts):
        entity_output = entity_output[0]
        entity_output[:, [0, -1]] -= np.inf
        entity_output[:, :, [0, -1]] -= np.inf
        entity_probs = softmax(entity_output, axis=1)
        ent_list = []
        for l, start, end in zip(*np.where(entity_output > 0.0)):
            ent_prob = entity_probs[l, start, end]
            start, end = (offset_mapping[start][0], offset_mapping[end][-1])
            ent = {
                "text": text[start:end],
                "type": label_maps["id2entity"][str(l)],
                "start_index": start,
                "end_index": end,
                "probability": ent_prob,
            }
            ent_list.append(ent)
        batch_ent_results.append((text, ent_list))
    return batch_ent_results

def _chunkify(
        text: str,
        chunk_token_len: int
) -> List[str]:
    if text is None or text.isspace():
        return []
    tokens = tokenizer.tokenize(text)
    chunks = []
    chunk_size = chunk_token_len
    num_chunks = 0
    while tokens and num_chunks < MAX_NUM_CHUNKS:
        chunk = tokens[:chunk_size]
        chunk_text = tokenizer.convert_tokens_to_string(chunk)
        if chunk_text is None or chunk_text.isspace():
            tokens = tokens[len(chunk) :]
            continue
        last_punctuation = max(
            chunk_text.rfind("."),
            chunk_text.rfind("?"),
            chunk_text.rfind("!"),
            chunk_text.rfind(";"),
            chunk_text.rfind("\n"),
            chunk_text.rfind("。"),
            chunk_text.rfind("？"),
            chunk_text.rfind("！"),
            chunk_text.rfind("…")
        )
        if last_punctuation != -1 and last_punctuation > MIN_CHUNK_SIZE_CHARS:
            chunk_text = chunk_text[: last_punctuation + 1]
        chunks.append(chunk_text)
        tokens = tokens[len(tokenizer.tokenize(chunk_text)) :]
        num_chunks += 1
    # if tokens:
    #     remaining_text = tokenizer.convert_tokens_to_string(tokens).replace("\n", " ").strip()
    #     chunks.append(remaining_text)
    return chunks    