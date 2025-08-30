from sentence_transformers import SentenceTransformer, util
import torch

model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer("nickprock/sentence-bert-base-italian-uncased")
    return model