import pandas as pd
from sentence_transformers import SentenceTransformer
import sqlite3
import numpy as np
import os

# 确保目录存在


# 1. 加载模型和数据
model = SentenceTransformer(r'/home/ubuntu/mnt2/wxy/Ako_GPT/sentence_transformers/all-MiniLM-L6-v2')
df = pd.read_csv(r'/home/ubuntu/mnt2/wxy/Ako_GPT/data/exam_entry_answer.csv', encoding='ISO-8859-1')

# 2. 创建数据库
DB_PATH = r'/home/ubuntu/mnt2/wxy/Ako_GPT/db_1/vector_store_1.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 删除已存在的表（如果需要重新创建）
cursor.execute('DROP TABLE IF EXISTS vector_store')

# 创建表
cursor.execute('''
CREATE TABLE vector_store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry TEXT,
    question TEXT,
    answer TEXT,
    question_embedding BLOB
)
''')

# 3. 处理每一行并存入数据库
for _, row in df.iterrows():
    # 格式化为问题文本
    question_text = f"The question id is {row['entry']}"
    
    # 只对问题部分生成向量
    question_embedding = model.encode(question_text)
    
    # 存入数据库
    cursor.execute(
        'INSERT INTO vector_store (entry, question, answer, question_embedding) VALUES (?, ?, ?, ?)',
        (row['entry'], question_text, row['answer'], question_embedding.tobytes())
    )

conn.commit()
conn.close()

print("Vector store created successfully!")