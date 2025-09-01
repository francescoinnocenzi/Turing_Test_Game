from sentence_transformers import SentenceTransformer
from typing import Optional

model: Optional[SentenceTransformer] = None

def get_model() -> SentenceTransformer:
    """
    Restituisce un'istanza del modello SentenceTransformer.
    Carica il modello solo la prima volta (lazy loading).
    
    Returns
        SentenceTransformer: Modello di embedding testuale.
    """
    global model
    if model is None:
        model = SentenceTransformer("nickprock/sentence-bert-base-italian-uncased")
    return model
