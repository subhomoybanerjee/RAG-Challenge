from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np

class EmbeddingManager:
    def __init__(self,model_name:str='multi-qa-mpnet-base-dot-v1'):
        self.model_name=model_name
        self.model=None
        self._load_model()

    def _load_model(self):
        try:self.model=SentenceTransformer(self.model_name)
        except Exception as e:print(f'problem: {e}')
    
    def generate_embedding(self,texts):
        if not self.model:raise ValueError('model not loaded.')
        embeddings=self.model.encode(texts,show_progress_bar=False)
        return np.array(embeddings)