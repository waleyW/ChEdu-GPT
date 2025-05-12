import os
import gradio as gr
import chromadb
from chromadb.config import Settings
from datetime import datetime
import shutil
from typing import Dict, List, Optional
from langchain.embeddings import OpenAIEmbeddings
import json

class ExamVectorDB:
    def __init__(self, persist_directory: str = "/ChEDdu_gpt/code/exam_vector_db"):
        """Initialize vector database"""
        self.persist_directory = os.path.abspath(persist_directory)
        
        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=self.persist_directory,
            anonymized_telemetry=False
        ))
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection("exam_info")
        except:
            self.collection = self.client.create_collection("exam_info")
        
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings()
    
    def add_exam_info(self, subject: str, exam_time: str, classroom: str, 
                     teacher: str, notes: str = "") -> str:
        """Add exam information to vector database"""
        # Combine information
        exam_info = (f"Subject: {subject}\nExam Time: {exam_time}\nClassroom: {classroom}\n"
                    f"Teacher: {teacher}\nNotes: {notes}")
        
        # Generate unique ID
        doc_id = f"exam_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate vector embedding
        embedding = self.embeddings.embed_query(exam_info)
        
        # Store in ChromaDB
        self.collection.add(
            documents=[exam_info],
            embeddings=[embedding],
            ids=[doc_id],
            metadatas=[{
                "subject": subject,
                "exam_time": exam_time,
                "classroom": classroom,
                "teacher": teacher,
                "notes": notes,
                "timestamp": datetime.now().isoformat()
            }]
        )
        
        return doc_id
    
    def search_exams(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search exam information"""
        query_embedding = self.embeddings.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )
        return results
    
    def get_db_info(self) -> dict:
        """Get database information"""
        size = sum(os.path.getsize(os.path.join(dirpath, filename))
                  for dirpath, _, filenames in os.walk(self.persist_directory)
                  for filename in filenames) / (1024 * 1024)  # MB
        
        return {
            "Database Location": self.persist_directory,
            "Database Size": f"{size:.2f} MB",
            "Number of Records": self.collection.count(),
            "Last Updated": datetime.fromtimestamp(
                os.path.getmtime(self.persist_directory)
            ).strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def backup_db(self, backup_dir: str = "./exam_db_backups") -> str:
        """Backup database"""
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(
            backup_dir,
            f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        shutil.copytree(self.persist_directory, backup_path)
        return backup_path

class ExamSystem:
    def __init__(self):
        self.db = ExamVectorDB()
        self.interface = self.create_interface()
    
    def validate_and_save(self, subject: str, exam_time: str, classroom: str,
                         teacher: str, notes: str) -> str:
        """Validate and save exam information"""
        # Validate required fields
        if not all([subject.strip(), exam_time.strip(), classroom.strip(), teacher.strip()]):
            return "Error: Subject, time, classroom and teacher are required fields!"
        
        try:
            doc_id = self.db.add_exam_info(subject, exam_time, classroom, teacher, notes)
            db_info = self.db.get_db_info()
            return (f"✅ Successfully added exam information!\n"
                   f"Document ID: {doc_id}\n"
                   f"Current database status:\n"
                   f"- Total records: {db_info['Number of Records']}\n"
                   f"- Database size: {db_info['Database Size']}")
        except Exception as e:
            return f"❌ Save failed: {str(e)}"
    
    def search_exam_info(self, query: str, show_details: bool = False) -> str:
        """Search exam information"""
        if not query.strip():
            return "Please enter search content"
        
        try:
            results = self.db.search_exams(query)
            output = "🔍 Search Results:\n\n"
            
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"],
                results["metadatas"],
                results["distances"]
            ), 1):
                relevance = 1 - (distance / 2)  # Convert distance to relevance score
                output += f"{i}. Relevance: {relevance:.2%}\n"
                output += f"{'='*50}\n"
                
                if show_details:
                    output += f"Subject: {metadata['subject']}\n"
                    output += f"Time: {metadata['exam_time']}\n"
                    output += f"Classroom: {metadata['classroom']}\n"
                    output += f"Teacher: {metadata['teacher']}\n"
                    if metadata['notes']:
                        output += f"Notes: {metadata['notes']}\n"
                    output += f"Record Time: {metadata['timestamp']}\n"
                else:
                    output += doc + "\n"
                
                output += "\n"
            
            return output
        except Exception as e:
            return f"❌ Search error: {str(e)}"
    
    def create_interface(self) -> gr.Blocks:
        """Create Gradio interface"""
        with gr.Blocks(title="Exam Information Management System") as interface:
            gr.Markdown("""
            # 📚 Exam Information Management System
            ### Instructions
            1. Fill in exam information in the "Add Exam Information" tab
            2. Query existing information in the "Search Exam Information" tab
            3. All fields marked with * are required
            """)
            
            with gr.Tabs():
                # Add exam information tab
                with gr.Tab("📝 Add Exam Information"):
                    with gr.Row():
                        with gr.Column():
                            subject = gr.Textbox(label="Subject*")
                            exam_time = gr.Textbox(label="Exam Time*", 
                                                 placeholder="e.g.: 2024-03-01 14:00")
                        with gr.Column():
                            classroom = gr.Textbox(label="Classroom*")
                            teacher = gr.Textbox(label="Teacher*")
                    
                    notes = gr.Textbox(label="Notes", lines=3)
                    submit_btn = gr.Button("Submit", variant="primary")
                    result = gr.Textbox(label="Result", lines=5)
                    
                    submit_btn.click(
                        fn=self.validate_and_save,
                        inputs=[subject, exam_time, classroom, teacher, notes],
                        outputs=result
                    )
                
                # Search exam information tab
                with gr.Tab("🔍 Search Exam Information"):
                    query = gr.Textbox(label="Search Content (Support fuzzy search)", 
                                     placeholder="e.g.: Math exam in March")
                    show_details = gr.Checkbox(label="Show detailed information")
                    search_btn = gr.Button("Search", variant="primary")
                    search_result = gr.Textbox(label="Search Results", lines=10)
                    
                    search_btn.click(
                        fn=self.search_exam_info,
                        inputs=[query, show_details],
                        outputs=search_result
                    )
                
                # Database information tab
                with gr.Tab("ℹ️ System Information"):
                    def get_info():
                        info = self.db.get_db_info()
                        return "\n".join(f"{k}: {v}" for k, v in info.items())
                    
                    info_btn = gr.Button("Refresh Information")
                    info_display = gr.Textbox(label="Database Information", lines=5)
                    backup_btn = gr.Button("Backup Database")
                    backup_result = gr.Textbox(label="Backup Result")
                    
                    info_btn.click(fn=get_info, outputs=info_display)
                    backup_btn.click(
                        fn=lambda: f"Backup saved to: {self.db.backup_db()}",
                        outputs=backup_result
                    )
        
        return interface
    
    def launch(self, **kwargs):
        """Launch application"""
        self.interface.launch(**kwargs)

def main():
    # Set OpenAI API key (in actual use, should be read from environment variables or config file)
    os.environ["OPENAI_API_KEY"] = "api"
    
    # Create and launch application
    app = ExamSystem()
    app.launch(share=True)

if __name__ == "__main__":
    main()
