import os
import chromadb
from langchain_core.documents import Document
import numpy as np
from pathlib import Path
import hashlib  # deterministic IDs ?

class vectorstore:
    def __init__(self, collection_name = 'pdf_documents', persist_directory = 'datasets/vdb'):
        self.collection_name = collection_name
        self.persist_directory = os.path.join(persist_directory, collection_name)
        self.client = None
        self.collection = None
        self.initialize_store()

    def initialize_store(self):
        os.makedirs(self.persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        existing_collections = [c.name for c in self.client.list_collections()]

        if self.collection_name in existing_collections:
            print(f"loading existing collection: {self.collection_name}")
            self.collection = self.client.get_collection(self.collection_name)
        else:
            print(f"creating new collection: {self.collection_name}")
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": f"{self.collection_name} embeddings for rag","hnsw:space": "cosine","store_embeddings": True}
            )

        print(f"Total documents: {self.collection.count()}")

        

    def get_existing_sources(self):
        if not self.collection or self.collection.count() == 0:
            return set()
        
        try:
            results = self.collection.get(include=["metadatas"])
            sources = set()
            for meta in results.get("metadatas", []):
                if meta and "source" in meta:
                    sources.add(meta["source"])
            return sources
        except Exception as e:
            print(f"problem: {e}")
            return set()

    def clear_collection(self):
        if self.collection is None:
            print("no collecs to clear.")
            return

        ids = self.collection.get()["ids"]
        if not ids:
            print(f"collec '{self.collection_name}' is already empty.")
            return

        print(f"delting all {len(ids)} entries from collection '{self.collection_name}'...")
        self.collection.delete(ids=ids)

        remaining = self.collection.count()
        print(f"collection  deleted. remaining: {remaining}")
    
    def filter_new_files(self, root_path):
        root_path = Path(root_path)
        candidate_files = []
        
        if root_path.is_file():
            candidate_files = [root_path]
        else:
            extensions = {".pdf", ".docx", ".doc"}
            candidate_files = [
                p for p in root_path.rglob("*") 
                if p.suffix.lower() in extensions and p.is_file()
            ]
            
        if not candidate_files:
            print("no PDF/Word in the path.")
            return []

        print("\nchecking vector store for existing files...")
        existing_sources = self.get_existing_sources()
        
        files_to_process = [f for f in candidate_files if f.name not in existing_sources]
        
        skipped_count = len(candidate_files) - len(files_to_process)
        if skipped_count > 0:print(f"skipping {skipped_count} files already indexed.")
        else:print("all found files are new.")
            
        return files_to_process
    
    def add_documents(self,documents,embeddings,batch_size = 5000,chunk_size = None,chunk_overlap = None):
        if len(documents) != len(embeddings):
            raise ValueError("num of documents and embeddings dont match.")

        print(f"adding {len(documents)} documents to the vector store ({self.collection_name})...")

        for start_idx in range(0, len(documents), batch_size):
            end_idx = start_idx + batch_size
            docs_batch = documents[start_idx:end_idx]
            embs_batch = embeddings[start_idx:end_idx]

            ids, metadatas, documents_texts, embeddings_list = [], [], [], []
            for i, (doc, embedding) in enumerate(zip(docs_batch, embs_batch)):
                
                content_hash = hashlib.md5(doc.page_content.encode('utf-8')).hexdigest()
                doc_id = f"doc_{content_hash}"
                
                ids.append(doc_id)

                metadata = dict(doc.metadata)
                metadata["content_length"] = len(doc.page_content)
                if chunk_size is not None:metadata["chunk_size"] = chunk_size
                if chunk_overlap is not None:metadata["chunk_overlap"] = chunk_overlap
                if chunk_size is not None:metadata["granularity"] = "fine" if chunk_size <= 120 else "coarse"

                metadatas.append(metadata)
                documents_texts.append(doc.page_content)
                embeddings_list.append(embedding.tolist())

            self.collection.upsert(ids=ids,metadatas=metadatas,documents=documents_texts,embeddings=embeddings_list)

        print(f"tote docs now in collection: {self.collection.count()}")


