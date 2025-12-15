from Utils import DataExtraction,Embedding,VectorStore,DataIngestion, Retrieval, Generation
from dataclasses import dataclass
from pathlib import Path
from langchain_groq import ChatGroq
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


@dataclass
class PipelineConfig:
    api_key: str = ''
    model_name: str = "llama-3.3-70b-versatile"
    temperature: float = 0.0
    chunk_size: int = 1200
    chunk_overlap: int = 250
    splitter_strategy: str = 'markdown'
    collection_name: str = 'Reports_docling'
    top_k: int = 8
    score_threshold: float = 0.1
    ocr_output_root: str = "debug/ocr_images_docling"

class RenewableDocumentEngine:
    def __init__(self, config):
        self.cfg = config
        self.initialize_components()
        self.qa_chain = None
        self.chat_history = []

    def initialize_components(self):
        logger.info(f"engine started with model: {self.cfg.model_name}")

        self.llm = ChatGroq(groq_api_key=self.cfg.api_key,model_name=self.cfg.model_name,temperature=self.cfg.temperature)
        self.embedding_manager = Embedding.EmbeddingManager()
        self.vectorstore = VectorStore.vectorstore(collection_name=self.cfg.collection_name)

    def ingest(self, doc_path):
        root_path = Path(doc_path)
        if not root_path.exists():
            raise FileNotFoundError(f"path not found: {root_path}")

        files_to_process = self.vectorstore.filter_new_files(root_path)
        total_docs_ingested = 0

        if files_to_process:
            logger.info(f"starting extraction for {len(files_to_process)} new files...")

            extractor = DataExtraction.Extractor(lang="multi",llm=self.llm,text_output_root=self.cfg.ocr_output_root)
            ingestor = DataIngestion.dataIngestion(embedding_manager=self.embedding_manager,vectorstore=self.vectorstore,default_chunk_size=self.cfg.chunk_size,default_chunk_overlap=self.cfg.chunk_overlap,splitter_strategy=self.cfg.splitter_strategy)

            for file_path in files_to_process:
                logger.info(f"extracting from: {file_path.name}")
                extracted_docs = extractor.process_file(file_path)

                if not extracted_docs:
                    logger.info(f"no documents extracted from: {file_path.name}")
                    continue

                logger.info(f"ingesting {len(extracted_docs)} documents from {file_path.name} into vector store...")
                ingestor.ingest_documents(extracted_docs)
                total_docs_ingested += len(extracted_docs)

                del extracted_docs

        else:
            logger.info("no new files to process.")

        if total_docs_ingested > 0:logger.info(f"total newly ingested documents: {total_docs_ingested}")
        else:logger.info("no new documents were ingested.")

        self.refresh_retriever()
        return f"Ingested {total_docs_ingested} documents."

    def refresh_retriever(self):
        logger.info("refreshing rag retriever...")
        rag_retriever = Retrieval.RAGretriever(self.vectorstore, self.embedding_manager, enable_reranking=True)
        self.qa_chain = Generation.generation(retriever=rag_retriever,llm=self.llm,default_top_k=self.cfg.top_k,score_threshold=self.cfg.score_threshold)

    def chat(self, query, history=None, use_reranking=False):
        if self.qa_chain is None:
            self.refresh_retriever()
            
        logger.info(f"querying: {query}")
        response = self.qa_chain.run(query=query, history=history, use_reranking=use_reranking)
        self.chat_history.append({"role": "user", "content": query})
        self.chat_history.append({"role": "assistant", "content": response['answer']})
        return response
    
    def clear_history(self):
        self.chat_history = []