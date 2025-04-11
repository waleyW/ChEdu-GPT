import pandas as pd 
from sentence_transformers import SentenceTransformer 
import sqlite3 
import numpy as np 

# 1. 加载数据并检查列名
df = pd.read_csv(r'/home/ubuntu/mnt2/wxy/Ako_GPT/data/exam_info.csv', encoding='ISO-8859-1')
print("CSV 文件的列名：")
print(df.columns.tolist())

# 2. 创建数据库 
conn = sqlite3.connect(r'/home/ubuntu/mnt2/wxy/Ako_GPT/db_1/information_Q.db') 
cursor = conn.cursor()  

# 3. 创建表来存储文本和向量 
cursor.execute(''' 
DROP TABLE IF EXISTS vector_store
''')

cursor.execute(''' 
CREATE TABLE IF NOT EXISTS vector_store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Subject TEXT,
    Exam_Time TEXT,
    Classroom TEXT,
    Teacher TEXT,
    Notes TEXT,
    formatted_text TEXT,
    embedding BLOB 
) 
''')  

# 加载模型
model = SentenceTransformer(r'/home/ubuntu/mnt2/wxy/Ako_GPT/sentence_transformers/all-MiniLM-L6-v2')

# 4. 处理每一行并存入数据库 
for _, row in df.iterrows():
    # 只对Subject生成向量
    subject_text = f"The class is {row['Subject']}"
    embedding = model.encode(subject_text)
    
    # 格式化完整文本（用于展示）     
    formatted_text = f"The class is {row['Subject']}, the exam time is {row['Exam_Time']}, the Classroom is {row['Classroom']}, the teacher is {row['Teacher']}, the notes is {row['Notes']}"
    
    # 存入数据库     
    cursor.execute(
        'INSERT INTO vector_store (Subject, Exam_Time, Classroom, Teacher, Notes, formatted_text, embedding) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (row['Subject'], row['Exam_Time'], row['Classroom'], row['Teacher'], row['Notes'], formatted_text, embedding.tobytes())
    )  

conn.commit() 
conn.close()  

print("Vector store created successfully!")