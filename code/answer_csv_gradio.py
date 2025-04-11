import gradio as gr
import pandas as pd
import os
from datetime import datetime

class AnswerCollector:
    def __init__(self, csv_path="/home/ubuntu/mnt2/ako_gpt/code/answers.csv"):
        self.csv_path = csv_path
        print(f"Initializing with CSV path: {self.csv_path}")
        
        # Create new CSV file with headers if it doesn't exist
        if not os.path.exists(csv_path):
            print(f"CSV file does not exist, creating new one...")
            df = pd.DataFrame(columns=['Question Number', 'Answer'])
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"Created new CSV file: {csv_path}")
    
    def validate_and_save(self, question_number: str, answer: str) -> str:
        """Validate input and save or update CSV file"""
        print(f"\nReceived new answer submission:")
        print(f"Question Number: {question_number}")
        
        # Validate required fields
        if not all([question_number.strip(), answer.strip()]):
            return "❌ Error: Question Number and Answer are required fields!"
        
        try:
            # Prepare new data
            new_data = {
                'Question Number': question_number.strip(),
                'Answer': answer.strip()
            }
            
            # Read existing CSV file
            try:
                df = pd.read_csv(self.csv_path, encoding='utf-8-sig')
                df['Question Number'] = df['Question Number'].astype(str)
            except FileNotFoundError:
                df = pd.DataFrame(columns=['Question Number', 'Answer'])
            
            # Check if question number exists and update
            mask = df['Question Number'].astype(str) == question_number.strip()
            if mask.any():
                # Delete old record
                df = df[~mask]
                # Add new record
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                update_type = "Updated"
                print(f"Updated existing answer for question: {question_number}")
            else:
                # Add new record
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                update_type = "Added"
                print(f"Added new answer for question: {question_number}")
            
            # Sort by question number
            df['Question Number'] = pd.to_numeric(df['Question Number'], errors='ignore')
            df = df.sort_values('Question Number').reset_index(drop=True)
            
            # Save to CSV
            df.to_csv(self.csv_path, index=False, encoding='utf-8-sig')
            
            return f"""✅ Successfully {update_type.lower()} answer!
            
Operation: {update_type} {'(Replaced existing answer)' if update_type == 'Updated' else '(New answer)'}
Total questions: {len(df)}
Latest information:
- Question Number: {question_number}
- Answer: {answer}

CSV file location: {self.csv_path}"""
            
        except Exception as e:
            return f"❌ Save failed: {str(e)}"
    
    def show_recent_records(self) -> str:
        """Display recent records"""
        try:
            df = pd.read_csv(self.csv_path, encoding='utf-8-sig')
            if len(df) == 0:
                return "No answers recorded yet"
            
            # Sort by question number and show all
            df['Question Number'] = pd.to_numeric(df['Question Number'], errors='ignore')
            df = df.sort_values('Question Number')
            
            formatted_output = "All Answers:\n"
            formatted_output += "=" * 50 + "\n"
            for _, row in df.iterrows():
                formatted_output += f"""
Question {row['Question Number']}:
Answer: {row['Answer']}
{"=" * 50}
"""
            return formatted_output
            
        except Exception as e:
            return f"Error reading records: {str(e)}"
    
    def create_interface(self) -> gr.Interface:
        """Create Gradio interface"""
        with gr.Blocks(title="Answer Collection System") as interface:
            gr.Markdown("""
            # 📝 Answer Collection System
            ### Instructions
            1. Both fields are required
            2. If a Question Number already exists, its answer will be updated
            3. All answers will be saved to a CSV file
            """)
            
            with gr.Row():
                question_number = gr.Textbox(
                    label="Question Number *",
                    placeholder="e.g., 1"
                )
                answer = gr.Textbox(
                    label="Answer *", 
                    placeholder="e.g., C",
                    lines=2
                )
            
            submit_btn = gr.Button(
                "Submit",
                variant="primary"
            )
            
            result = gr.Textbox(
                label="Result",
                lines=6
            )
            
            gr.Markdown("### All Answers")
            all_answers = gr.Textbox(
                label="Answer List",
                lines=15
            )
            refresh_btn = gr.Button("Refresh Answers")
            
            # Set event handlers
            submit_btn.click(
                fn=self.validate_and_save,
                inputs=[question_number, answer],
                outputs=result
            )
            
            refresh_btn.click(
                fn=self.show_recent_records,
                outputs=all_answers
            )
            
        return interface

def main():
    # Create collector instance
    collector = AnswerCollector()
    interface = collector.create_interface()
    
    # Launch interface
    interface.launch(share=True)

if __name__ == "__main__":
    main()