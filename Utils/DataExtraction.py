# import io
# import time
# from pathlib import Path
# import numpy as np
# import fitz  
# from PIL import Image
# from typing import List,Dict,Any,Tuple,Optional
# import os
# from langchain_core.documents import Document
# from io import BytesIO
# from docling.document_converter import DocumentConverter, PdfFormatOption
# from tempfile import NamedTemporaryFile

# from PIL import Image
# from contextlib import contextmanager


# @contextmanager
# def section_timer(label: str):
#     start = time.time()
#     try:yield
#     finally:
#         end = time.time()
#         duration = end - start
#         # nly print if it took noticeable time (e.g., > 0.1s)
#         if duration > 0.1: 
#             # print(f" [{label}] took {duration:.4f}s")
#             a=0

# # just docling
# class Extractor:
#     def __init__(self,lang,llm= None,text_output_root = None,translate= True,max_retries = 3):
#         self.lang = lang
#         self.llm = llm
#         self.text_output_root = Path(text_output_root) if text_output_root else None
#         self.translate = translate
#         self.max_retries = max_retries
        

#         print("initializing docling converter")
#         self.converter = DocumentConverter()

#     @staticmethod
#     def fix_image_colors(image):
#         if image.mode == "CMYK":
#             try:
#                 cmyk = np.array(image).astype(float)
#                 c, m, y, k = cmyk[..., 3], cmyk[..., 2], cmyk[..., 1], cmyk[..., 0]
                
#                 r = k - (c * (255 - k) / 255.0)
#                 g = k - (m * (255 - k) / 255.0)
#                 b = k - (y * (255 - k) / 255.0)
                
#                 rgb = np.dstack((r, g, b)).clip(0, 255).astype(np.uint8)
#                 image = Image.fromarray(rgb, mode='RGB')
#                 # print(" converted CMYK to RGB (my own formula).")
#             except Exception as e:
#                 image = image.convert("RGB")
#         return image
    
#     def run_docling_ocr(self, pil_image):
#         temp_path = None
#         try:
#             with NamedTemporaryFile(suffix=".png", delete=False, mode='wb') as tmp:
#                 pil_image.save(tmp)
#                 temp_path = tmp.name
            
#             result = self.converter.convert(temp_path)
#             return result.document.export_to_markdown()

#         except Exception as e:
#             print(f"docling problem: {e}")
#             return ""
#         finally:
#             if temp_path and os.path.exists(temp_path):
#                 try:os.unlink(temp_path)
#                 except Exception:pass

#     def process_image_single_engine(self, pil_image, save_dir, page_num):

#         with section_timer("CMYK conversion"): pil_image = self.fix_image_colors(pil_image)
#         with section_timer("docling ocr"):ocr_text = self.run_docling_ocr(pil_image).strip()
#         print(f'OCR len: {len(ocr_text)}')
#         if save_dir:
#             (save_dir / f"page_{page_num:03d}_docling.md").write_text(ocr_text, encoding="utf-8")
#         fo=ocr_text
#         return fo


#     def should_trigger_fallback(self, text, image_count):
#         clean_text = text.strip()
#         length = len(clean_text)
#         if length < 150:
#             print(f"low text density ({length} chars).")
#             return True

#         if image_count > 0 and length < 400:
#             print(f"image-heavy page ({image_count} imgs) with sparse text ({length} chars).")
#             return True
#         return False
    
    
#     def process_pdf(self, pdf_path):
#         pdf_path = Path(pdf_path)
#         doc_fitz = fitz.open(str(pdf_path))
#         pdf_name = pdf_path.stem
#         file_docs = []

#         save_dir = self.text_output_root / pdf_name if self.text_output_root else None
#         if save_dir: 
#             save_dir.mkdir(parents=True, exist_ok=True)
#             print(f"saving debug files to: {save_dir}")

#         print(f"processing {pdf_name} ({len(doc_fitz)} pages)...")

#         for i, page in enumerate(doc_fitz):
#             page_num = i + 1
#             fitz_page = doc_fitz[i]
            
#             raw_native = fitz_page.get_text() or ""
#             translated_native = ""

#             if raw_native.strip():
#                 print(f"page {page_num}] translating native text ({len(raw_native)} chars)...")
#                 translated_native = raw_native
            
#             image_list = fitz_page.get_images(full=True)
#             merged_image_texts = []
            
#             if image_list:
#                 for img_idx, img_info in enumerate(image_list):
#                     xref = img_info[0]
#                     base_img = fitz_page.parent.extract_image(xref)
#                     pil_image = Image.open(io.BytesIO(base_img["image"]))

#                     if pil_image.width < 100 and pil_image.height < 100:continue
                    
#                     if save_dir and pil_image.mode!='CMYK':pil_image.save(save_dir / f"p{page_num:03d}_img{img_idx}.png")

#                     img_result = self.process_image_single_engine(pil_image, save_dir, page_num)
                    
#                     if img_result.strip():
#                         block = f"--- [Image {img_idx} Content] ---\n{img_result}"
#                         merged_image_texts.append(block)
            
#             # fallback 
#             current_content_len = len(translated_native) + sum(len(t) for t in merged_image_texts)
#             current_text_snapshot = translated_native + "\n".join(merged_image_texts)
#             if self.should_trigger_fallback(current_text_snapshot, len(image_list)):
                
#                 print(f"page got low quality text. running full page screenshot ocr.")
                
#                 try:
#                     pix = fitz_page.get_pixmap(matrix=fitz.Matrix(2, 2))
#                     full_page_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
#                     with section_timer("orientation check full SS"):full_page_img = self.fix_orientation(full_page_img) 
                    
#                     if save_dir:
#                         fallback_path = save_dir / f"p{page_num:03d}_fallback_screenshot.png"
#                         full_page_img.save(fallback_path)
                    
#                     full_ocr_text = self.run_docling_ocr(full_page_img)
                    
#                     if len(full_ocr_text) > current_content_len:
#                         print(f"fallback recovered {len(full_ocr_text)} chars (was {current_content_len}).")
#                         if self.translate and self.llm:
#                              translated_ocr = full_ocr_text
#                              translated_native = translated_ocr 
#                         else:
#                              translated_native = full_ocr_text
#                         merged_image_texts = [] 
#                     else:
#                         print(f"fallback disregarded (screenshot yielded less text than before).")
#                         pass

#                 except Exception as e:
#                     print(f"fallback failed: {e}")
#                     pass


#             final_content_parts = []
            
#             if translated_native:final_content_parts.append(translated_native)
            
#             if merged_image_texts:final_content_parts.append("\n\n".join(merged_image_texts))
            
#             final_text = "\n\n".join(final_content_parts)

#             if save_dir:
#                 (save_dir / f"page_{page_num:03d}_final.md").write_text(final_text, encoding="utf-8")

#             if final_text.strip():
#                 meta = {"source": pdf_path.name, "page": page_num, "images_found": len(image_list)}
#                 file_docs.append(Document(page_content=final_text, metadata=meta))

#         doc_fitz.close()
#         return file_docs

#     def process_docx(self, doc_path):
        
#         doc_path = Path(doc_path)
#         doc_name = doc_path.stem
#         file_docs = []

#         save_dir = self.text_output_root / doc_name if self.text_output_root else None
#         if save_dir:
#             save_dir.mkdir(parents=True, exist_ok=True)
#             print(f"saving debug files to: {save_dir}")

#         print(f"processing Word document {doc_name}...")

#         try:
#             result = self.converter.convert(str(doc_path))
#             dl_doc = result.document
#             md = dl_doc.export_to_markdown()

#             if save_dir:
#                 (save_dir / f"{doc_name}_docling.md").write_text(md, encoding="utf-8")

#             if md.strip():
#                 meta = {
#                     "source": doc_path.name,
#                     "file_type": "docx" if doc_path.suffix.lower() == ".docx" else "doc",
#                 }
#                 file_docs.append(Document(page_content=md, metadata=meta))
#             print('done\n')

#         except Exception as e:
#             print(f"docling failed on {doc_path.name}: {e}")

#         return file_docs

#     def process_file(self, path):
        
#         path = Path(path)
#         ext = path.suffix.lower()

#         if ext == ".pdf":
#             return self.process_pdf(path)
#         elif ext in (".docx", ".doc"):
#             return self.process_docx(path)
#         else:
#             raise ValueError(f"nope, use .pdf or .docx or .doc files only: {ext} ({path})")

#     def process_directory(self, path):
#         print(path)
#         path = Path(path)
#         docs = []

#         if path.is_file():
#             return self.process_file(path)

#         if path.is_dir():
#             for f in path.glob("**/*"):
#                 if f.suffix.lower() in (".pdf", ".docx", ".doc"):
#                     try:
#                         docs.extend(self.process_file(f))
#                     except Exception as e:
#                         print(f"Error {f.name}: {e}")
#         return docs

from pathlib import Path
import fitz  
from langchain_core.documents import Document
from docling.document_converter import DocumentConverter


# docling only for word, no ocr
class Extractor:
    def __init__(self,lang,llm= None,text_output_root = None,translate= True,max_retries = 3):
        self.lang = lang
        self.llm = llm
        self.text_output_root = Path(text_output_root) if text_output_root else None
        self.translate = translate
        self.max_retries = max_retries
        print("initializing docling converter")
        self.converter = DocumentConverter()
        
    def process_pdf(self, pdf_path):
        pdf_path = Path(pdf_path)
        doc_fitz = fitz.open(str(pdf_path))
        pdf_name = pdf_path.stem
        file_docs = []

        save_dir = self.text_output_root / pdf_name if self.text_output_root else None
        if save_dir: 
            save_dir.mkdir(parents=True, exist_ok=True)
            print(f"saving debug files to: {save_dir}")

        print(f"processing {pdf_name} ({len(doc_fitz)} pages)...")

        for i, page in enumerate(doc_fitz):
            page_num = i + 1
            fitz_page = doc_fitz[i]
            
            raw_native = fitz_page.get_text() or ""
            translated_native = ""

            if raw_native.strip():
                print(f"page {page_num}] translating native text ({len(raw_native)} chars)...")
                translated_native = raw_native
            
            final_content_parts = []
            if translated_native:final_content_parts.append(translated_native)
            final_text = "\n\n".join(final_content_parts)

            if save_dir:
                (save_dir / f"page_{page_num:03d}_final.md").write_text(final_text, encoding="utf-8")

            if final_text.strip():
                meta = {"source": pdf_path.name, "page": page_num}
                file_docs.append(Document(page_content=final_text, metadata=meta))

        doc_fitz.close()
        return file_docs

    def process_docx(self, doc_path):
        
        doc_path = Path(doc_path)
        doc_name = doc_path.stem
        file_docs = []

        save_dir = self.text_output_root / doc_name if self.text_output_root else None
        if save_dir:
            save_dir.mkdir(parents=True, exist_ok=True)
            print(f"saving debug files to: {save_dir}")

        print(f"processing Word document {doc_name}...")

        try:
            result = self.converter.convert(str(doc_path))
            dl_doc = result.document
            md = dl_doc.export_to_markdown()

            if save_dir:
                (save_dir / f"{doc_name}_docling.md").write_text(md, encoding="utf-8")

            if md.strip():
                meta = {
                    "source": doc_path.name,
                    "file_type": "docx" if doc_path.suffix.lower() == ".docx" else "doc",
                }
                file_docs.append(Document(page_content=md, metadata=meta))
            print('done\n')

        except Exception as e:
            print(f"docling failed on {doc_path.name}: {e}")

        return file_docs

    def process_file(self, path):
        
        path = Path(path)
        ext = path.suffix.lower()

        if ext == ".pdf":
            return self.process_pdf(path)
        elif ext in (".docx", ".doc"):
            return self.process_docx(path)
        else:
            raise ValueError(f"nope, use .pdf or .docx or .doc files only: {ext} ({path})")

    def process_directory(self, path):
        print(path)
        path = Path(path)
        docs = []

        if path.is_file():
            return self.process_file(path)

        if path.is_dir():
            for f in path.glob("**/*"):
                if f.suffix.lower() in (".pdf", ".docx", ".doc"):
                    try:
                        docs.extend(self.process_file(f))
                    except Exception as e:
                        print(f"Error {f.name}: {e}")
        return docs
