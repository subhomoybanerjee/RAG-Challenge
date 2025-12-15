# import streamlit as st
# from main import RenewableDocumentEngine, PipelineConfig  

# st.set_page_config(page_title="local rag engine", layout="wide")
# st.title("rag")
# MAX_MESSAGES = 40

# def add_message(role: str, content: str):
#     st.session_state.messages.append({"role": role, "content": content})
#     if len(st.session_state.messages) > MAX_MESSAGES:
#         st.session_state.messages = st.session_state.messages[-MAX_MESSAGES:]

# with st.sidebar:
#     st.header("Configuration")
#     api_key = st.text_input("Groq API Key", type="password")
#     doc_path = st.text_input("Document Folder", value="datasets/files")
    
#     if st.button("ingest documents/reload"):
#         if not api_key:
#             st.error("please enter API first.")
#         else:
#             with st.spinner("scanning and ingesting"):
#                 config = PipelineConfig(
#                     api_key=api_key,
#                     model_name="llama-3.3-70b-versatile",
#                     ocr_output_root="debug/ocr_images"
#                 )
#                 engine = RenewableDocumentEngine(config)
#                 status_msg = engine.ingest(doc_path)
                
#                 st.session_state['engine'] = engine
#                 st.success(f"ingestion complete! {status_msg}")

# if "messages" not in st.session_state:
#     st.session_state.messages = []

# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# if prompt := st.chat_input("ask a question about your files..."):
#     add_message("user", prompt)
#     with st.chat_message("user"):
#         st.markdown(prompt)

#     if 'engine' in st.session_state:
#         with st.chat_message("assistant"):
#             with st.spinner("thinking"):
#                 try:
#                     response_payload = st.session_state['engine'].chat(
#                         query=prompt, 
#                         history=st.session_state.messages[:-1] 
#                     )
                    
#                     answer_text = response_payload['answer']
#                     sources = response_payload.get('sources', [])
#                     context = response_payload.get('context', "")

#                     st.markdown(answer_text)
                    
#                     if sources:
#                         unique_sources = list(set(sources))
#                         st.caption(f"Sources: {', '.join(unique_sources)}")
                    
#                     with st.expander("view retrieved context"):
#                         st.text(context)

#                     add_message("assistant", answer_text)
                    
#                 except Exception as e:
#                     st.error(f"problem: {e}")
#     else:
#         st.error("run ingestion from the sidebar first.")