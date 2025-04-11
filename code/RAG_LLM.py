import pandas as pd
import sqlite3

# 读取CSV文件
csv_file_path = r'/home/ubuntu/mnt2/wxy/Ako_GPT/data/exam.xlsx'  # 替换为您的CSV文件路径
data = pd.read_excel(csv_file_path)

# 连接到SQLite数据库，如果没有则创建
conn = sqlite3.connect('questions.db')
cursor = conn.cursor()

# 创建表格（如果表格不存在）
cursor.execute('''
CREATE TABLE IF NOT EXISTS questions (
    entry TEXT PRIMARY KEY,
    answer TEXT
)
''')

# 将CSV数据插入到数据库中
for index, row in data.iterrows():
    cursor.execute('INSERT OR IGNORE INTO questions (entry, answer) VALUES (?, ?)', (row['entry'], row['answer']))

# 提交更改
conn.commit()

# 定义检索答案的函数
def get_answer(entry_id):
    cursor.execute("SELECT answer FROM questions WHERE entry=?", (entry_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        return "未找到该题号。"

# 示例使用
entry_id = input("请输入题号: ")
answer = get_answer(entry_id)
print(f"答案: {answer}")

# 关闭数据库连接
conn.close()
