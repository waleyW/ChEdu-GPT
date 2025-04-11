import pandas as pd
import sqlite3
import re
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import gradio as gr

# 读取CSV文件，指定编码格式
csv_file_path = r'/home/ubuntu/mnt2/wxy/Ako_GPT/data/exam_entry_answer.csv'  # 替换为您的CSV文件路径
data = pd.read_csv(csv_file_path, encoding='ISO-8859-1')  # 可以使用 'latin1' 或 'gbk' 作为替代

# 初始化数据库并插入数据的函数
def initialize_database():
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS questions (
        entry TEXT PRIMARY KEY,
        answer TEXT
    )
    ''')
    # 将CSV数据插入到数据库中
    for index, row in data.iterrows():
        cursor.execute('INSERT OR IGNORE INTO questions (entry, answer) VALUES (?, ?)', (row['entry'], row['answer']))
    conn.commit()
    conn.close()

# 初始化数据库
initialize_database()

# 根据题号检索答案的函数
def get_answer(entry_id):
    conn = sqlite3.connect('questions.db')
    cursor = conn.cursor()
    cursor.execute("SELECT answer FROM questions WHERE entry=?", (entry_id,))
    result = cursor.fetchone()
    conn.close()
    print(f"Retrieved answer: {result}")  # 调试输出
    if result:
        return result[0]
    else:
        return None


# 加载LLM模型的函数
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

# 加载模型
model_path = r'/home/ubuntu/mnt2/wxy/model/Mistral-7B-Instruct-v0.3'  
model, tokenizer, device = load_model(model_path)

# 处理输入并调用LLM生成回答的函数
def ask(text):
    if not isinstance(text, str):  # Ensure the input is a string
        return "Input text must be a valid string."

    instruction_prefix = (
        "<s>[INST] <<SYS>>\n"
        "You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.\n\n"
        "If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.\n"
        "<</SYS>> \n\n"
    )
    
    pdf_text = ''  # Placeholder as pdf extraction is not currently implemented
    
    # 从用户的输入中提取题号并检索答案
    match = re.search(r'question ID is ([\w-]+)', text)
    if match:
        entry_id = match.group(1)
        answer = get_answer(entry_id)
        if answer:
            combined_prompt = f"{instruction_prefix}{pdf_text}\n\nquestion ID is {entry_id}'s answer: {answer}\n\nuser question: {text}[/INST]"
        else:
            combined_prompt = f"{instruction_prefix}{pdf_text}{text} [/INST]"
    else:
        combined_prompt = f"{instruction_prefix}{pdf_text}{text} [/INST]"

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

# Custom CSS for styling
custom_css = """
#title {
    text-align: center;
    color: #4a4a4a;
    padding: 20px 0;
    background-color: #f0f0f0;
    border-bottom: 2px solid #ddd;
    margin-bottom: 20px;
}
.feature-box {
    background-color: #e9f7fe;
    border: 1px solid #b3e5fc;
    border-radius: 5px;
    padding: 15px;
    margin-bottom: 20px;
}
"""

# Gradio Web Interface
with gr.Blocks(css=custom_css) as server:
    gr.Markdown("# Ako-GPT", elem_id="title")  # Add title at the top

    with gr.Tab("LLM Inferencing"):
        # Add feature introduction box
        gr.Markdown(
            """
            <div class="feature-box">
            <strong>Feature Introduction:</strong>
            <ol>
                <li>Supports answering existing questions on Piazza (under optimization)</li>
                <li>Supports answering exam-related questions. <strong>If you want to ask for answers to exam questions, please follow the format: question ID is xxxx (for example: CHEM251_2023_Exam-1-b-2)</strong></li>
                <li>Supports answering basic chemistry knowledge questions</li>
            </ol>
            </div>
            """,
            elem_classes=["feature-box"]
        )

        model_input = gr.Textbox(label="Your Question:", placeholder="Enter your question here", interactive=True)
        ask_button = gr.Button("Ask")
        model_output = gr.Textbox(label="The Answer:", interactive=False, placeholder="The answer will appear here...")
        
        ask_button.click(fn=ask, inputs=model_input, outputs=model_output)
    
    # Add disclaimer at the bottom
    with gr.Row():
        gr.Markdown("---")  # Horizontal line for separation
    with gr.Accordion("Disclaimer", open=False):
        gr.Markdown(disclaimer_text)

server.launch(share=True)