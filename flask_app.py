from flask import Flask, request, jsonify,send_from_directory
from flask_cors import CORS
from main import RenewableDocumentEngine, PipelineConfig
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# app = Flask(__name__)
app = Flask(__name__, static_folder='build/static', template_folder='build')
CORS(app) 
engine_instance = None

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path.startswith('api/'):
        return jsonify({"error": "Not found"}), 404
        
    if path != "" and os.path.exists(os.path.join(app.template_folder, path)):
        return send_from_directory(app.template_folder, path)
        
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/ingest', methods=['POST'])
def ingest_documents():
    global engine_instance
    
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        doc_path = data.get('doc_path', 'datasets/files')
        model_name = data.get('model_name', 'llama-3.3-70b-versatile')
        
        if not api_key:
            return jsonify({"error": "API ?????"}), 400
        
        logger.info(f"starting ingestion for path: {doc_path}")
        
        config = PipelineConfig(api_key=api_key,model_name=model_name,ocr_output_root="debug/ocr_images")
        
        engine_instance = RenewableDocumentEngine(config)
        status_msg = engine_instance.ingest(doc_path)
        
        return jsonify({
            "success": True,
            "message": status_msg
        }), 200
        
    except Exception as e:
        logger.error(f"error during ingestion: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    global engine_instance
    
    try:
        data = request.get_json()
        query = data.get('query')
        history = data.get('history', [])
        use_reranking = data.get('use_reranking', False)
        
        if not query:
            return jsonify({"error": "query is required"}), 400
        
        if engine_instance is None:
            return jsonify({"error": "run ingestion first"}), 400
        
        logger.info(f"processing query: {query}")
        
        response_payload = engine_instance.chat(query=query,history=history,use_reranking=use_reranking)
        
        return jsonify({
            "success": True,
            "answer": response_payload['answer'],
            "sources": response_payload.get('sources', []),
            "context": response_payload.get('context', '')
        }), 200
        
    except Exception as e:
        logger.error(f"error during chat: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    global engine_instance
    
    try:
        if engine_instance:
            engine_instance.clear_history()
        return jsonify({"success": True, "message": "history cleared"}), 200
    except Exception as e:
        logger.error(f"error clearing history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    global engine_instance
    
    return jsonify({
        "engine_initialized": engine_instance is not None,
        "has_qa_chain": engine_instance.qa_chain is not None if engine_instance else False
    }), 200

@app.route('/api/clear-vector-db', methods=['POST'])
def clear_vector_db():
    global engine_instance
    
    try:
        if engine_instance is None:
            return jsonify({"error": "engine not initialized"}), 400
        
        engine_instance.vectorstore.clear_collection()
        
        engine_instance.refresh_retriever()
        
        return jsonify({
            "success": True,
            "message": "vector database cleared successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"error clearing vector database: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True,use_reloader=False, host='0.0.0.0', port=5000)

