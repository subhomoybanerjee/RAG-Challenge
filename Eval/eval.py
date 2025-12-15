import os
import sys
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import logging
from main import RenewableDocumentEngine, PipelineConfig
from Utils import Evaluation  

logging.basicConfig(level=logging.CRITICAL) 

def load_test_cases(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:return json.load(f)

def main():
    Apeeai='' # add your own api key here from groq
    model_name='llama-3.1-8b-instant'
    # model_name='llama-3.3-70b-versatile'
    api_key = os.getenv("API_KEY", Apeeai)
    
    config = PipelineConfig(api_key=api_key,model_name=model_name,ocr_output_root="../debug/eval_ocr",top_k= 5, score_threshold = 0.1)
    engine = RenewableDocumentEngine(config)
    engine.ingest(doc_path="../datasets/files")
    engine.refresh_retriever()
    test_cases = load_test_cases("datasets/evalQuestions.json")
    
    use_reranking = True  
    evaluator = Evaluation.RAGEvaluator(engine, use_reranking=use_reranking)
    df = evaluator.run_eval_suite(test_cases)

    print("evaluation results:")
    
    cols = ["question", "correctness", "faithfulness", "context_rel", "answer_rel", "ground_truth"]
    print(df[cols].to_string(index=False))

    if not df.empty:
        print(f"avg correctness:      {df['correctness'].mean():.1f}")
        print(f"avg faithfulness:     {df['faithfulness'].mean():.1f}")
        print(f"avg context rel:      {df['context_rel'].mean():.1f}")
        print(f"avg answer rel:       {df['answer_rel'].mean():.1f}")
    
    df.to_csv("evaluation_report.csv", index=False)
    print("\nfull report saved to the same direc 'evaluation_report.csv'")

main()