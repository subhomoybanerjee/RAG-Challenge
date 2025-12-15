import pandas as pd
import re
import time

class RAGEvaluator:
    def __init__(self, engine, use_reranking=False):
        self.engine = engine
        self.judge_llm = engine.llm
        self.use_reranking = use_reranking 

    def extract_score(self,llm_output):
        try:
            match = re.search(r'\d+', llm_output)
            if match:
                score = int(match.group())
                return min(max(score, 0), 10)
            return 0
        except Exception:return 0

    def evaluate_correctness(self, question, ground_truth, ai_answer):
        prompt = f"""
        You are a strict teacher grading an exam.
        Question: {question}
        Ground Truth: {ground_truth}
        Student Answer: {ai_answer}
        
        Grade from 0 to 10 based on accuracy.
        - 10: Perfect match with the Ground Truth.
        - 0: Completely wrong or irrelevant.
        - If Ground Truth is "Unknown" and Student says "I don't know", give 10.
        
        Return ONLY the number.
        """
        try:
            time.sleep(4)
            res = self.judge_llm.invoke(prompt)
            content = res.content if hasattr(res, 'content') else str(res)
            return self.extract_score(content)
        except:return 0

    def evaluate_faithfulness(self, context, ai_answer):
        prompt = f"""
        You are a fact-checker. Determine if the Statement is supported by the Context.
        
        [Context]
        {context[:10000]} 
        
        [Statement]
        {ai_answer}
        
        Grade from 0 (Hallucination) to 10 (Fully Supported).
        - If the statement contains facts NOT in the context, score 0.
        - If statement says "I don't know" because context is missing, score 10.
        
        Return ONLY the number.
        """
        try:
            time.sleep(4)
            res = self.judge_llm.invoke(prompt)
            content = res.content if hasattr(res, 'content') else str(res)
            return self.extract_score(content)
        except:return 0

    def evaluate_context_relevance(self, question, context):
        if not context.strip():return 0 
        prompt = f"""
        You are an Information Retrieval expert. 
        
        User Question: {question}
        
        Retrieved Documents:
        {context[:10000]}
        
        Task: Rate how relevant the Retrieved Documents are to the Question.
        - Score 10: The documents contain the exact answer.
        - Score 5: The documents talk about the topic but don't have the specific answer.
        - Score 0: The documents are completely unrelated noise.
        
        Return ONLY the number (0-10).
        """
        try:
            time.sleep(4)
            res = self.judge_llm.invoke(prompt)
            content = res.content if hasattr(res, 'content') else str(res)
            return self.extract_score(content)
        except:return 0

    def evaluate_answer_relevance(self, question: str, ai_answer: str) -> int:
        prompt = f"""
        You are a conversational analyst.
        
        User Question: {question}
        AI Answer: {ai_answer}
        
        Task: Rate how relevant the AI Answer is to the User Question.
        - Ignore if the answer is factually true or false. Focus ONLY on directness.
        - Score 10: Direct, specific answer to the question.
        - Score 0: The AI is talking about something completely different.
        
        Return ONLY the number (0-10).
        """
        try:
            time.sleep(4)
            res = self.judge_llm.invoke(prompt)
            content = res.content if hasattr(res, 'content') else str(res)
            return self.extract_score(content)
        except:return 0

    def run_eval_suite(self, test_cases):
        results = []
        print(f"evaluating {len(test_cases)} cases...\n")

        for i, case in enumerate(test_cases):
            q = case['question']
            truth = case['ground_truth']
            
            print(f"[{i+1}/{len(test_cases)}] Asking: {q}")

            time.sleep(5)
            response_payload = self.engine.chat(query=q, history=[], use_reranking=self.use_reranking)
            
            ai_answer = response_payload.get('answer', "")
            context = response_payload.get('context', "")
            
            c_score = self.evaluate_correctness(q, truth, ai_answer)
            f_score = self.evaluate_faithfulness(context, ai_answer)
            cr_score = self.evaluate_context_relevance(q, context)
            ar_score = self.evaluate_answer_relevance(q, ai_answer)
            
            results.append({"question": q,"ai_answer": ai_answer,"correctness": c_score,"faithfulness": f_score,"context_rel": cr_score,"answer_rel": ar_score,"ground_truth": truth})
        return pd.DataFrame(results)