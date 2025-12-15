class generation:
    def __init__(self,retriever,llm,default_top_k = 20,score_threshold = 0):
        self.retriever = retriever
        self.llm = llm
        self.default_top_k = default_top_k
        self.score_threshold = score_threshold

    def build_prompt(self, query, context, history_str):
        
        prompt = "You are a helpful AI assistant. "
        
        if context.strip():
            print('Context was able to be extracted based on query')
            prompt += "Answer the question using the [Context] provided below.\n"
        else:
            print('Context was not found based on user query, answering basing on LLMs knowledge.')
            prompt += "Answer based on your own knowledge as no context was found.\n"

        prompt += f"""
        [Conversation History]
        {history_str}

        [Retrieved Context]
        {context}

        [User's Question]
        {query}

        Answer:"""
        return prompt

    def call_llm(self, prompt):
        resp = self.llm.invoke(prompt)
        return resp if isinstance(resp, str) else resp.content
    
    def format_history(self, history):
        if not history:
            return ""
            
        lines = []
        for turn in history[-6:]:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            prefix = "USER" if role == "user" else "ASSISTANT"
            lines.append(f"{prefix}: {content}")
        
        return "\n".join(lines)

    def run(self,query,history = None,top_k = None,use_reranking=False):
        k = top_k or self.default_top_k
        results= self.retriever.retrieve(query,top_k=k,score_threshold=self.score_threshold,use_reranking=use_reranking)

        context_parts = []
        sources = set()
        if results:
            for i, doc in enumerate(results):
                content = doc.get("content", "")
                meta = doc.get("metadata", {})
                source = meta.get("source", "Unknown Source")
                page = meta.get("page", "N/A")
                # formatted_chunk = f"[[Source File Name: {source} | Page: {page}]]\n{content}" # for debugging
                formatted_chunk = f"{content}"
                context_parts.append(formatted_chunk)
                if source and source != "Unknown Source":
                    sources.add(source)
            
            context = "\n\n--\n\n".join(context_parts)
        else:context = ""
        
        history_str = self.format_history(history or [])

        prompt = self.build_prompt(query, context,history_str)
        answer = self.call_llm(prompt)
        
        return {"answer": answer,"context": context,"sources": list(sources)}

    def __call__(self, query, top_k = None):
        return self.run(query, top_k=top_k)