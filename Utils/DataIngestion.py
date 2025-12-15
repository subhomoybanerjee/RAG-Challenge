from langchain_text_splitters import RecursiveCharacterTextSplitter, Language


class dataIngestion:  
    def __init__(
        self,embedding_manager,vectorstore,
        default_chunk_size= 1000,default_chunk_overlap = 100,language= Language.MARKDOWN,
        splitter_strategy = "markdown",  # "markdown" or "generic"
        separators = None,length_function= len,
    ):
        self.embedding_manager = embedding_manager
        self.vectorstore = vectorstore
        self.default_chunk_size = default_chunk_size
        self.default_chunk_overlap = default_chunk_overlap
        self.language = language
        self.splitter_strategy = splitter_strategy.lower()
        self.separators = separators or ["\n\n", "\n", " ", ""]
        self.length_function = length_function

    def _build_splitter(self,chunk_size,chunk_overlap,strategy = None):
        strat = (strategy or self.splitter_strategy).lower()
        if strat == "markdown":
            return RecursiveCharacterTextSplitter.from_language(language=self.language,chunk_size=chunk_size,chunk_overlap=chunk_overlap,length_function=self.length_function)
        if strat == "generic":
            return RecursiveCharacterTextSplitter(chunk_size=chunk_size,chunk_overlap=chunk_overlap,length_function=self.length_function,separators=self.separators,)

    def split_documents(self,documents,chunk_size = None,chunk_overlap = None,strategy = None):
        cs = chunk_size or self.default_chunk_size
        co = chunk_overlap or self.default_chunk_overlap

        text_splitter = self._build_splitter(chunk_size=cs,chunk_overlap=co,strategy=strategy)

        documents = list(documents)
        split_docs = text_splitter.split_documents(documents)

        print(f"Split {len(documents)} documents into {len(split_docs)} chunks (chunk_size={cs}, overlap={co}, strategy={strategy or self.splitter_strategy})")
        return split_docs

    def embed_chunks(self, chunks):
        if not chunks:return []
            
        texts = [doc.page_content for doc in chunks]
        embeddings = self.embedding_manager.generate_embedding(texts)
        return embeddings

    def add_chunks_to_vectorstore(self,chunks,embeddings=None,chunk_size = None,chunk_overlap = None):
        if not chunks:return

        cs = chunk_size or self.default_chunk_size
        co = chunk_overlap or self.default_chunk_overlap

        if embeddings is None:
            embeddings = self.embed_chunks(chunks)

        self.vectorstore.add_documents(
            chunks,
            embeddings,
            chunk_size=cs,
            chunk_overlap=co,
        )
        print(f"added {len(chunks)} chunks to vectorstore (chunk_size={cs}, overlap={co})")

    def ingest_documents(self, documents):
        chunks = self.split_documents(documents)
        self.add_chunks_to_vectorstore(chunks)

    def process_chunk_sets(self,documents,chunk_sets,strategy = None):
        documents = list(documents)
        all_chunks_by_config = {}

        for cs, co in chunk_sets:
            print(f"\nadding chunk set: [{cs}, {co}]")
            chunks = self.split_documents(documents,chunk_size=cs,chunk_overlap=co,strategy=strategy)
            
            if chunks:
                embeddings = self.embed_chunks(chunks)
                self.add_chunks_to_vectorstore(chunks,embeddings=embeddings,chunk_size=cs,chunk_overlap=co)
                all_chunks_by_config[(cs, co)] = chunks

        return all_chunks_by_config
