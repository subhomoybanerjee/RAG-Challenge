# RAG

A Retrieval-Augmented Generation system built with Flask backend and React frontend 

### [Click here to see the deployed pipeline on GCP (can take a little time to load.)](https://chatty-1062294228986.us-central1.run.app)

## Features

- Document Processing: Support for PDF and DOCX files with OCR capabilities for image-based documents if gpu setup during prod in GCP
- Vector-based Retrieval: ChromaDB-powered semantic search with optional cross-encoder reranking and BM25.
- Chat Interface: React-based UI with real-time conversation display
- LLM Integration: Groq API integration.
- Reranking Toggle: Enable or disable cross-encoder reranking for retrieval results dynamically
- Vector Database Management: Clear all indexed documents from the vector store with a single action
- Evaluation Framework: Included evaluation metrics for assessing RAG system performance
- Persistent Storage: ChromaDB vector store with incremental updates
- Incremental Ingestion: File filtering to avoid reprocessing existing documents

## Table of Contents

- Architecture
- Prerequisites
- Installation
- Configuration
- Usage
- API Documentation
- Evaluation
- Trade-offs 
- Project Structure
- Troubleshooting

## Architecture

It follows a modular architecture with separation between the user interface, API layer, and core processing components.

The React frontend communicates with the Flask backend via HTTP/JSON. The backend processes requests through the RAG Engine, which handles document extraction, embedding generation, vector storage, retrieval, and response generation. All vector data is stored in ChromaDB.

### Components

1. Data Extraction (Utils/DataExtraction.py): Extracts text from PDF and DOCX files using Docling with OCR fallback for image-based content (Only if gpu is setup, else it would take loads of time on the free tier.)
2. Data Ingestion (Utils/DataIngestion.py): Processes documents, applies text chunking strategies, and prepares content for vector storage
3. Embedding (Utils/Embedding.py): Generates semantic embeddings using sentence transformers for similarity search
4. Vector Store (Utils/VectorStore.py): Manages ChromaDB operations including document indexing, querying, and deduplication
5. Retrieval (Utils/Retrieval.py): Performs semantic search with initial vector retrieval followed by optional cross-encoder reranking
6. Generation (Utils/Generation.py): Generates contextual responses using LLM with retrieved context and conversation history

## Prerequisites

### Backend Requirements
- Python 3.13.2
- pip package manager
- Groq API key (available from Groq Console, bring your own api.)

### Frontend Requirements
- Node.js

## Installation

### 1. Backend Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

### 3. Frontend Setup

Navigate to the frontend directory and install dependencies:

```bash
cd frontend
npm install
```


## Configuration

### Pipeline Configuration

The RAG pipeline can be configured in main.py through the PipelineConfig class. The following parameters are available:

- api_key: Groq API key
- model_name: LLM model identifier, default is "llama-3.3-70b-versatile" (only use models from Groq)
- temperature: LLM temperature parameter controlling response randomness, default is 0.1
- chunk_size: Size of document chunks in characters, default is 1200
- chunk_overlap: Overlap between chunks for context preservation, default is 250
- splitter_strategy: Text splitting method, default is 'markdown'
- collection_name: ChromaDB collection name, default is 'Reports_docling'
- top_k: Number of document chunks to retrieve per query, default is 8
- score_threshold: Minimum relevance score for retrieved chunks, default is 0.1
- ocr_output_root: Directory path for debug, contains OCR/Text output files, default is "debug/ocr_images_docling"


## Usage

### Starting the Application

#### Manual Start

Start the Flask backend in one terminal:

```bash
python flask_app.py
```

Start the React frontend in another terminal:

```bash
cd frontend
npm start
```

#### Windows Batch Scripts

You can use the provided batch scripts on Windows:

For the backend:
```bash
start_backend.bat
```

For the frontend:
```bash
start_frontend.bat
```

For running the evaluation suite:
```bash
run_evaluator.bat
```

### Accessing the Application

The frontend interface is available at http://localhost:3000 in your web browser. The backend API runs on http://localhost:5000.

### Basic Workflow

1. Start both the Flask backend and React frontend services
2. Open the application in your web browser
3. Enter your Groq API key in the configuration sidebar
4. Specify the folder path containing your documents (default path is datasets/files)
5. Click "Ingest Documents" to process and index your files
6. Once ingestion completes, the engine status will show "Engine Ready for RAG"
7. Optionally enable reranking using the checkbox in the sidebar for improved retrieval accuracy
8. Begin asking questions about your documents
9. Use "Clear History" to reset conversation context
10. Use "Clear Vector DB" to remove all indexed documents from the vector store

### Document Preparation

Place your documents in the datasets/files directory. The system supports PDF files (.pdf) and Word documents (.docx, .doc). Right now has the documents - attention is all you need, eu ai act.

Example directory structure:

```
datasets/files/
├── document1.pdf
├── document2.docx
└── document3.pdf
```


## API Documentation

### Base URL

```
http://localhost:5000/api
```

### Endpoints

#### Health Check

GET /health

Check if the API service is running and responsive.

#### Get Engine Status

GET /status

Retrieve the current status of the RAG engine, including whether it is initialized and ready to process queries.

#### Ingest Documents

POST /ingest

Process and index documents from a specified directory path. This endpoint extracts text, generates embeddings, and stores documents in the vector database.

Error responses will include an error field with a descriptive message.

#### Chat Query

POST /chat

Send a query to the RAG system and receive a response based on the indexed documents.

Parameters:
- query: Required. The question or query text
- history: Optional. Array of conversation history messages with role and content fields
- use_reranking: Optional. Boolean flag to enable cross-encoder reranking for retrieval results, default is false


#### Clear Chat History

POST /clear-history

Clear the conversation history maintained by the engine instance.

#### Clear Vector Database

POST /clear-vector-db

Remove all indexed documents from the ChromaDB vector store. This action permanently deletes all embeddings and metadata. The engine must be initialized before using this endpoint.

After clearing the vector database, you will need to ingest documents again before querying.

## Evaluation

This includes an evaluation framework for assessing RAG system performance. This can help measure answer quality, retrieval accuracy, and overall system effectiveness.

### Running Evaluation

Navigate to the Eval directory and run the evaluation script:

```bash
cd Eval
python eval.py
```

Alternatively, on Windows you can use the provided batch script:

```bash
run_evaluator.bat
```

The evaluation script supports enabling or disabling reranking. Edit the use_reranking variable in Eval/eval.py to control this behavior.

### Evaluation Metrics

The evaluation framework reports several metrics:

- Correctness: Measures the accuracy of generated answers
- Faithfulness: Evaluates whether answers are grounded in the retrieved context
- Context Relevance: Assesses how relevant the retrieved context is to the query
- Answer Relevance: Measures how relevant the answer is to the original question

### Evaluation Data Format

Prepare evaluation questions in Eval/datasets/evalQuestions.json using the following format:

```json
[
  {
    "question": "What is X?",
    "ground_truth": "X is..."
  }
]
```

Each test case requires two fields:
- question: The question to evaluate against the RAG system
- ground_truth: Ideal answer used for correctness evaluation

The evaluation results are saved to evaluation_report.csv for further analysis.

### Evaluation Results CSV Format

The evaluation report is saved as a CSV file named `evaluation_report.csv` in the Eval directory. The CSV contains the following columns:

- **question**: The original question that was evaluated
- **ai_answer**: The answer generated by the RAG system for the question
- **correctness**: Score from 0 to 10 measuring how accurate the AI answer is compared to the ground truth
- **faithfulness**: Score from 0 to 10 indicating whether the answer is supported by the retrieved context (0 = hallucination, 10 = fully supported)
- **context_rel**: Score from 0 to 10 measuring how relevant the retrieved context is to the question (10 = contains exact answer, 0 = unrelated)
- **answer_rel**: Score from 0 to 10 measuring how directly the AI answer addresses the question (10 = direct answer, 0 = unrelated)
- **ground_truth**: The expected or ideal answer for comparison

All scores are integers ranging from 0 to 10.

## Trade-offs & Design Decisions

This section outlines key architectural choices and the trade-offs considered during system design.

### Text Preprocessing Pipeline

**Decision**: Minimal text cleaning during extraction, markdown-aware chunking, and normalization only for BM25 indexing.

**Preprocessing Steps**:

1. **Document Extraction**:
   - PDF files: Direct text extraction using PyMuPDF (fitz) with no additional cleaning
   - DOCX files: Conversion to markdown format using Docling, preserving document structure
   - Text is extracted as-is and saved to markdown files for debugging purposes

2. **Text Chunking**:
   - Uses RecursiveCharacterTextSplitter from LangChain with configurable strategy
   - **Markdown-aware splitting** (default): Respects markdown structure, splits on markdown syntax boundaries (headers, lists, paragraphs)
   - **Generic splitting**: Uses hierarchical separators `["\n\n", "\n", " ", ""]` to split while preserving sentence boundaries (NOT used for this app, but can switch to it, for experimenting.)
   - Default chunk size: 1200 characters with 250 character overlap

3. **Text Normalization (BM25 Only)**:
   - Applied only to text used for BM25 lexical search indexing
   - **Lowercasing**: All text converted to lowercase for case-insensitive matching
   - **Punctuation removal**: All punctuation characters replaced with spaces
   - **Whitespace tokenization**: Text split on whitespace to create tokens
   - Note: Vector embeddings use original text without normalization to preserve semantic meaning

4. **Metadata Processing**:
   - Content length tracking for each chunk
   - Chunk size and overlap metadata stored with documents
   - Granularity classification: "fine" (≤120 chars) or "coarse" (>120 chars)
   - Source file name and page number tracking for citation

**Trade-offs**:
- **Advantages**: Preserves original text quality for semantic embeddings, markdown splitting maintains document structure, minimal preprocessing reduces information loss, BM25 normalization improves keyword matching
- **Disadvantages**: No spell checking or typo correction, no stop word removal (may add noise to BM25), no stemming or lemmatization (different word forms treated separately), original text storage requires more disk space

**Rationale**: The preprocessing strategy prioritizes information preservation over aggressive cleaning. Vector embeddings benefit from original text quality, while BM25 benefits from simple normalization.

### Flask Backend with React Frontend

**Decision**: Separate Flask backend API with React frontend instead of a single Streamlit application.

**Trade-offs**:
- **Advantages**: Better separation of concerns, enables frontend backend independent scaling, more flexible UI customization, prodready architecture, allows mobile app development
- **Disadvantages**: Increased complexity, requires managing two services, more setup overhead compared to Streamlit's single-file approach

**Rationale**: While Streamlit offers rapid prototyping, the Flask React architecture provides better scalability and flexibility for prod deployments and allows the backend to serve multiple clients.

### ChromaDB for Vector Storage

**Decision**: Use ChromaDB as the embedded vector database stored locally on disk.

**Trade-offs**:
- **Advantages**: Simple setup with no external dependencies, persistent storage across restarts, efficient cosine similarity search, automatic embedding storage
- **Disadvantages**: Not Scalable.

**Rationale**: ChromaDB offers a good balance of simplicity and functionality for local and small to medium scale deployments. For larger scale, migration to distributed vector databases like Pinecone would be necessary.

### Hybrid Retrieval: Vector Search + BM25

**Decision**: Combine semantic vector search with BM25 and merge results before reranking.

**Trade-offs**:
- **Advantages**: Captures both semantic meaning (vector search) and exact keyword matches (BM25), improves recall by retrieving from both methods, handles out-of-vocabulary terms better than pure vector search
- **Disadvantages**: Increased computational overhead, requires maintaining both retrieval systems, potential redundancy in merged results

**Rationale**: Hybrid retrieval addresses the limitations of pure semantic search (missing exact keyword matches) and pure lexical search (missing semantic relationships). The combination significantly improves retrieval quality, especially for technical documents with domain specific terms.

### Optional Cross-Encoder Reranking

**Decision**: Make cross-encoder reranking optional and controllable via user toggle, with lazy model loading.

**Trade-offs**:
- **Advantages**: Better ranking accuracy when enabled, users can trade accuracy for speed, lazy loading saves memory when reranking is disabled, improves precision of final results
- **Disadvantages**: Additional latency when enabled, requires loading an additional model, increased memory usage during reranking

**Rationale**: Reranking significantly improves retrieval quality but adds latency. Making it optional allows users to choose based on their needs, disable for faster responses, enable for better accuracy. Lazy loading ensures the reranker model is only loaded when needed.

### Docling for Document Extraction with OCR

**Decision**: Use Docling for document extraction with OCR fallback for image-based PDFs.(NOT INCLUDED AS OF NOW)

**Trade-offs**:
- **Advantages**: High-quality text extraction, preserves document structure, handles complex layouts better than basic PDF parsers, OCR support for scanned documents
- **Disadvantages**: OCR processing is slow without GPU acceleration and can be impractical on CPU-only environments

**Rationale**: Docling provides superior extraction quality for structured documents. OCR is included for completeness but with clear documentation that GPU is recommended for production use.


### Evaluation Framework with LLM-as-Judge

**Decision**: Use the same LLM as a judge for evaluation metrics (correctness, faithfulness, relevance).

**Trade-offs**:
- **Advantages**: Automated evaluation without human annotators, hence scalable.
- **Disadvantages**: May have biases from using the same model after all its using ai to judge ai, subjective scoring may vary, requires LLM API calls for each evaluation which adds evaluation time and cost

**Rationale**: Manual evaluation is not scalable for large test suites.



```
Inference/
├── flask_app.py              # Flask backend API server
├── main.py                   # Core RAG engine and PipelineConfig class
├── app_streamlit_OPTIONAL.py # Streamlit application (optional alternative, faster debug)
│
├── Utils/                    # Core utility modules
│   ├── DataExtraction.py     # Document extraction processing
│   ├── DataIngestion.py      # Document processing and text chunking
│   ├── Embedding.py          # Embedding generation using sentence transformers
│   ├── VectorStore.py        # ChromaDB vector store operations
│   ├── Retrieval.py          # Semantic search and cross-encoder reranking
│   ├── Generation.py         # LLM response generation with context
│   └── Evaluation.py         # RAG evaluation framework and metrics
│
├── frontend/                 # React frontend application
│   ├── public/
│   │   └── index.html        # HTML template
│   ├── src/
│   │   ├── App.js            # Main application component
│   │   ├── App.css           # Application styles
│   │   ├── index.js          # React application entry point
│   │   ├── components/
│   │   │   ├── Sidebar.js    # Configuration sidebar component
│   │   │   ├── ChatInterface.js  # Chat user interface component
│   │   │   └── Message.js    # Individual message display component
│   │   └── services/
│   │       └── api.js        # API client service for backend communication
│   └── package.json          # Node.js dependencies and scripts
│
├── datasets/                 # Data storage directories
│   ├── files/                # Place documents for ingestion here
│   └── vdb/                  # Vector database storage location
│
├── debug/                    # Debug and OCR output directories
│   ├── ocr_images/           # OCR processed images and text output
│   └── eval_ocr/             # Same as ocr_images, but contains debugs from the eval.py
│
├── Eval/                     # Evaluation framework
│   ├── eval.py               # Main evaluation script
│   ├── datasets/
│   │   ├── evalQuestions.json  # Evaluation question datasets
|   |   └── vdb/                # Vector database for evaluation
│   └── evaluation_report.csv   # Generated evaluation results
│
├── requirements.txt          # Python package dependencies
├── start_backend.bat         # Windows batch script to start backend
├── start_frontend.bat        # Windows batch script to start frontend
├── run_evaluator.bat         # Windows batch script to run evaluation
└── README.md                 # This documentation file
```
