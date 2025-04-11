import gradio as gr
import pandas as pd
import os
from datetime import datetime

class ExamInfoCollector:
    def __init__(self, csv_path="/home/ubuntu/mnt2/ako_gpt/code/exam_info.csv"):
        self.csv_path = csv_path
        print(f"Initializing with CSV path: {self.csv_path}")
        
        # Create new CSV file with headers if it doesn't exist
        if not os.path.exists(csv_path):
            print(f"CSV file does not exist, creating new one...")
            df = pd.DataFrame(columns=['Subject', 'Exam Time', 'Classroom', 'Teacher', 'Notes'])
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"Created new CSV file: {csv_path}")
    
    def validate_and_save(self, subject: str, exam_time: str, classroom: str,
                     teacher: str, notes: str = "") -> str:
        """Validate input and save or update CSV file"""
        print(f"\nReceived new data submission:")
        print(f"Subject: {subject}")
        
        # Validate required fields
        if not all([subject.strip(), exam_time.strip(), classroom.strip(), teacher.strip()]):
            return "❌ Error: Subject, Exam Time, Classroom, and Teacher are required fields!"
        
        try:
            # Prepare new data
            new_data = {
                'Subject': subject.strip(),
                'Exam Time': exam_time.strip(),
                'Classroom': classroom.strip(),
                'Teacher': teacher.strip(),
                'Notes': notes.strip()
            }
            
            # Read existing CSV file
            try:
                df = pd.read_csv(self.csv_path, encoding='utf-8-sig')
                # 确保Subject列是字符串类型
                df['Subject'] = df['Subject'].astype(str)
            except FileNotFoundError:
                df = pd.DataFrame(columns=['Subject', 'Exam Time', 'Classroom', 'Teacher', 'Notes'])
            
            # 修复: 检查科目是否存在并更新
            mask = df['Subject'].astype(str) == subject.strip()
            if mask.any():
                # 删除旧记录
                df = df[~mask]
                # 添加新记录
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                update_type = "Updated"
                print(f"Updated existing record for subject: {subject}")
            else:
                # 添加新记录
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                update_type = "Added"
                print(f"Added new record for subject: {subject}")
            
            # 保存到CSV
            df.to_csv(self.csv_path, index=False, encoding='utf-8-sig')
            
            return f"""✅ Successfully {update_type.lower()} exam information!
            
    Operation: {update_type} {'(Replaced existing record)' if update_type == 'Updated' else '(New record)'}
    Total records: {len(df)}
    Latest information:
    - Subject: {subject}
    - Exam Time: {exam_time}
    - Classroom: {classroom}
    - Teacher: {teacher}
    - Notes: {notes}
    
    CSV file location: {self.csv_path}"""
            
        except Exception as e:
            return f"❌ Save failed: {str(e)}"
    
    def show_recent_records(self) -> str:
        """Display recent records with update time"""
        try:
            df = pd.read_csv(self.csv_path, encoding='utf-8-sig')
            if len(df) == 0:
                return "No records found"
            
            # Sort by most recent first (if you have a timestamp column)
            # For now, we'll just show the last 5 records
            recent = df.tail(5)
            
            formatted_output = "Recent Records:\n"
            formatted_output += "=" * 80 + "\n"
            for _, row in recent.iterrows():
                formatted_output += f"""
Subject: {row['Subject']}
Exam Time: {row['Exam Time']}
Classroom: {row['Classroom']}
Teacher: {row['Teacher']}
Notes: {row['Notes']}
{"=" * 80}
"""
            return formatted_output
            
        except Exception as e:
            return f"Error reading records: {str(e)}"
    
    def create_interface(self) -> gr.Interface:
        """Create Gradio interface"""
        with gr.Blocks(title="Exam Information Collection System") as interface:
            gr.Markdown("""
            # 📚 Exam Information Collection System
            ### Instructions
            1. Fields marked with * are required
            2. If a Subject already exists, its information will be updated
            3. All information will be saved to a CSV file
            4. Please ensure correct time format (Recommended: YYYY-MM-DD HH:MM)
            """)
            
            with gr.Row():
                with gr.Column():
                    subject = gr.Textbox(
                        label="Subject *",
                        placeholder="e.g., Advanced Mathematics"
                    )
                    exam_time = gr.Textbox(
                        label="Exam Time *", 
                        placeholder="e.g., 2024-03-25 14:00"
                    )
                with gr.Column():
                    classroom = gr.Textbox(
                        label="Classroom *",
                        placeholder="e.g., Science Building 301"
                    )
                    teacher = gr.Textbox(
                        label="Teacher *",
                        placeholder="e.g., Mr. Smith"
                    )
            
            notes = gr.Textbox(
                label="Notes",
                placeholder="Optional: Add exam-related instructions",
                lines=3
            )
            
            submit_btn = gr.Button(
                "Submit",
                variant="primary"
            )
            
            result = gr.Textbox(
                label="Result",
                lines=6
            )
            
            gr.Markdown("### Recent Records")
            recent_records = gr.Textbox(
                label="Recently Added/Updated Exam Information",
                lines=12
            )
            refresh_btn = gr.Button("Refresh Records")
            
            # Set event handlers
            submit_btn.click(
                fn=self.validate_and_save,
                inputs=[subject, exam_time, classroom, teacher, notes],
                outputs=result
            )
            
            refresh_btn.click(
                fn=self.show_recent_records,
                outputs=recent_records
            )
            
        return interface

def main():
    # Create collector instance
    collector = ExamInfoCollector()
    interface = collector.create_interface()
    
    # Launch interface
    interface.launch(share=True)

if __name__ == "__main__":
    main()