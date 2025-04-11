import pandas as pd
import sqlite3
import re
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import gradio as gr
import os
import numpy as np
from sentence_transformers import SentenceTransformer

# 全局变量定义
DB_PATH = r'/home/ubuntu/mnt2/wxy/Ako_GPT/db_1/vector_store_1.db'
COURSE_DB_PATH = r'/home/ubuntu/mnt2/wxy/Ako_GPT/db_1/information_Q.db'
st_model = SentenceTransformer(r'/home/ubuntu/mnt2/wxy/Ako_GPT/sentence_transformers/all-MiniLM-L6-v2')
import os
print(f"Database file exists: {os.path.exists(COURSE_DB_PATH)}")
print(f"Database file permissions: {oct(os.stat(COURSE_DB_PATH).st_mode)[-3:]}")
# 全局提示词定义
INSTRUCTION_PREFIX = (
    "<s>[INST] <<SYS>>\n"
    "You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. "
    "Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. "
    "Please ensure that your responses are socially unbiased and positive in nature.\n\n"
    "If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. "
    "If you don't know the answer to a question, please don't share false information.\n"
    "<</SYS>> \n\n"
)

def load_model(model_path):
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    
    if torch.cuda.is_available():
        device = torch.device("cuda")
        torch_dtype = torch.float16
    else:
        device = torch.device("cpu")
        torch_dtype = torch.float32

    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch_dtype
    ).to(device)
    
    return model, tokenizer, device

model_path = r'/home/ubuntu/mnt2/wxy/model/Mistral-7B-Instruct-v0.3'  
model, tokenizer, device = load_model(model_path)

def query_answer(text):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 生成查询向量
        query_vector = st_model.encode(text)
        
        # 获取所有问题向量
        cursor.execute("SELECT entry, question, answer, question_embedding FROM vector_store")
        results = cursor.fetchall()
        
        # 计算相似度
        valid_similarities = []  # 只存储有效的结果
        for entry, question, answer, stored_vector in results:
            if stored_vector is not None and question is not None and answer is not None:
                vector = np.frombuffer(stored_vector, dtype=np.float32)
                similarity = float(np.dot(query_vector, vector))
                print(f"Similarity with {entry}: {similarity}")
                valid_similarities.append([similarity, question, answer])
        
        if valid_similarities:
            sorted_similarities = sorted(valid_similarities, key=lambda x: x[0], reverse=True)
            best_match = sorted_similarities[0]
            
            if best_match[0] > 0.7:
                return {
                    'question': best_match[1],
                    'answer': best_match[2],
                    'similarity': best_match[0]
                }
        return None
        
    except Exception as e:
        print(f"Error in question query: {e}")
        return None
    finally:
        if conn:
            conn.close()
            
def query_course_info(text):
    conn = None
    try:
        conn = sqlite3.connect(COURSE_DB_PATH)
        cursor = conn.cursor()
        
        subject_query = "The class is " + text.split("The Class is")[1].split(",")[0].strip()
        query_vector = st_model.encode(subject_query)
        
        # 修改这里的 SQL 查询，将 subject_embedding 改为 embedding
        cursor.execute("""
            SELECT Subject, Exam_Time, Classroom, Teacher, Notes, formatted_text, embedding 
            FROM vector_store""")
        results = cursor.fetchall()
        
        valid_similarities = []
        for subject, exam_time, classroom, teacher, notes, formatted_text, stored_vector in results:
            if stored_vector is not None:
                vector = np.frombuffer(stored_vector, dtype=np.float32)
                similarity = float(np.dot(query_vector, vector))
                print(f"Similarity with {subject}: {similarity}")
                valid_similarities.append([similarity, subject, exam_time, classroom, teacher, notes, formatted_text])
        
        if valid_similarities:
            sorted_similarities = sorted(valid_similarities, key=lambda x: x[0], reverse=True)
            best_match = sorted_similarities[0]
            
            if best_match[0] > 0.7:
                return {
                    'subject': best_match[1],
                    'exam_time': best_match[2],
                    'classroom': best_match[3],
                    'teacher': best_match[4],
                    'notes': best_match[5],
                    'formatted_text': best_match[6],
                    'similarity': best_match[0]
                }
        return None
              
    except Exception as e:
        print(f"Error in course query: {e}")
        return None
    finally:
        if conn:
            conn.close()

def ask(text):
    if not isinstance(text, str):
        return "Input text must be a valid string."

    # 情况1: 课程查询
    if text.startswith("The Class is"):
        course_info = query_course_info(text)
        if course_info:
            combined_prompt = f"{INSTRUCTION_PREFIX}Based on the course information:\n" \
                            f"{course_info['formatted_text']}\n\n" \
                            f"Please provide a helpful and friendly response to: {text}[/INST]"
        else:
            combined_prompt = f"{INSTRUCTION_PREFIX}I apologize, but I couldn't find information for the requested course. " \
                            f"Please verify the course name and try again.[/INST]"
    
    # 情况2: 问题ID查询
    elif text.lower().startswith("question id is"):
        print(f"\nProcessing question query: {text}")
        qa_info = query_answer(text)
        print(f"Query result: {qa_info}")
        
        if qa_info and isinstance(qa_info, dict):
            print(f"Found match with similarity: {qa_info.get('similarity', 'N/A')}")
            print(f"Question: {qa_info.get('question', 'N/A')}")
            print(f"Answer: {qa_info.get('answer', 'N/A')}")
            
            # 直接使用问题和答案的内容，不要让LLM重新解释
            return f"Question ID: {qa_info['question']}\nAnswer: {qa_info['answer']}"
            
            # 或者如果你想保持prompt格式：
            combined_prompt = f"{INSTRUCTION_PREFIX}Here is the exact answer for your question:\n\n" \
                             f"Question id: {qa_info['question']}\n" \
                             f"Answer: {qa_info['answer']}\n\n" \
                             f"Please provide this answer to the user.[/INST]"
        else:
            combined_prompt = f"{INSTRUCTION_PREFIX}I cannot find a matching question in the database. " \
                             f"Please verify the question ID and try again.[/INST]"
    
    # 情况3: 直接LLM回答
    else:
        combined_prompt = f"{INSTRUCTION_PREFIX}{text}[/INST]"

    # 生成回答
    inputs = tokenizer(combined_prompt, return_tensors='pt').to(device)
    input_length = inputs.input_ids.shape[1]
    outputs = model.generate(**inputs, max_new_tokens=2000, temperature=0.7, return_dict_in_generate=True)
    tokens = outputs.sequences[0, input_length:]
    return tokenizer.decode(tokens)


# Disclaimer text
disclaimer_text = """
This LLM (Large Language Model) inferencing tool is provided for educational and research purposes only. Please read and understand the following disclaimers before using this service:

1. The responses generated by this AI model are not guaranteed to be accurate, complete, or suitable for any specific purpose.
2. Users are solely responsible for verifying and validating any information or suggestions provided by the AI model.
3. This service should not be used as a substitute for professional advice in any field, including but not limited to medical, legal, financial, or educational matters.
4. The developers and operators of this service are not responsible for any consequences resulting from the use of the information provided by the AI model.
5. User data may be collected and processed for the purpose of improving the service. By using this tool, you consent to such data collection and processing.
6. The service may be interrupted, terminated, or modified at any time without prior notice.
7. Users are prohibited from using this service for any illegal, unethical, or harmful purposes.
8. Personal data has been processed and sensitive information has been removed.

By using this LLM inferencing tool, you acknowledge that you have read, understood, and agreed to this disclaimer.
"""

# Feature introduction text
feature_intro = """
## ChEdu-GPT Features:

1. **Answer Piazza Questions**: Supports answering existing questions from Piazza (under optimization).

2. **Exam Question Assistance**: Provides help with exam-related questions. 
   **If you want to ask for answers to exam questions, please follow the format: question ID is xxxx (for example: CHEM251_2023_Exam-1-b-2)**

3. **Course Schedule Query**: Check course schedules by asking "The Class is [CLASS_NAME], may I know the schedule"

4. **Basic Chemistry Knowledge**: Offers support for fundamental chemistry concepts and questions.
"""

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the image file
image_path = os.path.join(script_dir, "ako-gpt-logo.png")

# Gradio Web Interface
with gr.Blocks() as server:
    with gr.Row():
        gr.Image(image_path, show_label=False, width=50)
        gr.Markdown("# ChEdu-GPT")
    
    gr.Markdown(feature_intro)
    
    gr.Markdown("<br>")  # Add some space

    with gr.Tab("LLM Inferencing"):
        model_input = gr.Textbox(label="Your Question:", placeholder="Enter your question here", interactive=True)
        ask_button = gr.Button("Ask")
        model_output = gr.Textbox(label="The Answer:", interactive=False, placeholder="The answer will appear here...")
        
        ask_button.click(fn=ask, inputs=model_input, outputs=model_output)
    
    # Add some vertical space
    for _ in range(3):
        gr.Markdown("<br>")
    
    # Add disclaimer at the bottom
    with gr.Row():
        gr.Markdown("---")  # Horizontal line for separation
    with gr.Accordion("Disclaimer", open=False):
        gr.Markdown(disclaimer_text)

server.launch(share=True)