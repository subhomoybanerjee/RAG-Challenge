import numpy as np
import string
from rank_bm25 import BM25Okapi

def simple_tokenize(text):
    text = text.lower()
    text = text.translate(str.maketrans(string.punctuation, ' ' * len(string.punctuation)))
    return text.split()

class RAGretriever:
    def __init__(self, vector_store, embedding_manager, rerank_model_name='cross-encoder/ms-marco-MiniLM-L-6-v2', enable_reranking=True):
        self.vector_store = vector_store
        self.embedding_manager = embedding_manager
        self.rerank_model_name = rerank_model_name
        self.enable_reranking = enable_reranking
        self.reranker = None  
        all_docs = self.vector_store.collection.get() 
        self.bm25_corpus = all_docs.get('documents', [])
        self.bm25_ids = all_docs.get('ids', [])
        self.bm25_metadatas = all_docs.get('metadatas', [])
        
        if len(self.bm25_corpus) > 0:
            self.tokenized_corpus = [simple_tokenize(doc) for doc in self.bm25_corpus]
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        else:
            self.tokenized_corpus = []
            self.bm25 = None 
    
    def _get_reranker(self):
        if self.reranker is None:
            if self.enable_reranking:
                from sentence_transformers import CrossEncoder
                print(f"Loading reranker model: {self.rerank_model_name}")
                self.reranker = CrossEncoder(self.rerank_model_name)
            else:
                raise ValueError("reranking is disabled. enable it in __init__ to use reranking.")
        return self.reranker

    def retrieve(self, query, top_k = 5, score_threshold = 0.5, n_candidates = 300,use_reranking = False ):
        
        if len(self.bm25_corpus) == 0:
            print("vector database is empty. no documents to retrieve.")
            return []
        
        current_n_candidates = n_candidates if use_reranking else top_k * 2
        fetch_k = max(1, current_n_candidates // 2)  
        query_embedding = self.embedding_manager.generate_embedding([query])[0]
        vector_results = self.vector_store.collection.query(query_embeddings=[query_embedding.tolist()],n_results=fetch_k)
        tokenized_query = simple_tokenize(query)
        bm25_docs = self.bm25.get_top_n(tokenized_query, self.bm25_corpus, n=fetch_k) if self.bm25 else []
        
        bm25_candidates = []
        for doc in bm25_docs:
            try:
                idx = self.bm25_corpus.index(doc)
                bm25_candidates.append({"id": self.bm25_ids[idx],"content": self.bm25_corpus[idx],"metadata": self.bm25_metadatas[idx],"source": "bm25"})
            except Exception as e:print(f'problem: {e}')

        candidates = {}
        
        if vector_results["documents"]:
            for i, doc_id in enumerate(vector_results["ids"][0]):
                candidates[doc_id] = {"id": doc_id,"content": vector_results["documents"][0][i],"metadata": vector_results["metadatas"][0][i],"source": "vector"}
                
        for item in bm25_candidates:
            if item["id"] not in candidates:
                candidates[item["id"]] = item
                
        final_candidates_list = list(candidates.values())

        if not final_candidates_list:
            print("no documents found from either source.")
            return []

        if use_reranking:
            print(f"reranking {len(final_candidates_list)} candidates")
            reranker = self._get_reranker()
            rerank_pairs = [[query, c["content"]] for c in final_candidates_list]
            
            scores = reranker.predict(rerank_pairs)
            prob_scores = 1 / (1 + np.exp(-scores)) 

            for i, candidate in enumerate(final_candidates_list):
                candidate['similarity_score'] = float(prob_scores[i])

            filtered = [d for d in final_candidates_list if d["similarity_score"] > score_threshold]
            filtered.sort(key=lambda d: d["similarity_score"], reverse=True)
            
            final_docs = filtered[:top_k]

        else:
            print("not going for reranking, returning raw retrieval results.")
            final_docs = final_candidates_list[:top_k]

        print(f"final payload: {len(final_docs)} documents sent to LLM.")
        
        return final_docs