from sentence_transformers import SentenceTransformer
model = None

def get_model():
    global model
    if model is None:
        model = SentenceTransformer("nickprock/sentence-bert-base-italian-uncased")
    return model