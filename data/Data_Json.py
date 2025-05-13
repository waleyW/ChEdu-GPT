import os
import re
import json

def parse_conversation_to_instructional_format(file_content):
    """Convert dialogue format to instructional format"""
    
    # Use regex to extract dialogue turns
    turns = re.findall(r'(Student|Instructor): (.*?)(?=\n\n(?:Student|Instructor):|$)', file_content, re.DOTALL)
    
    # If no dialogue format is found, return empty list
    if not turns:
        return []
    
    # Create training data instances
    training_data = []
    
    # For each instructor response after a student question, create a training instance
    for i in range(0, len(turns)-1, 2):
        if turns[i][0] == "Student" and i+1 < len(turns) and turns[i+1][0] == "Instructor":
            student_text = turns[i][1].strip()
            instructor_text = turns[i+1][1].strip()
            
            # Collect previous dialogue history
            history = ""
            if i > 0:
                for j in range(0, i):
                    role = turns[j][0]
                    text = turns[j][1].strip()
                    history += f"Previous {role.lower()}: {text}\n"
            
            # Create instruction based on dialogue stage
            if i == 0:
                instruction = "As a chemistry education assistant, when students express confusion about chemical concepts, use the Socratic method to guide their thinking rather than providing direct answers. Ask questions that help students explore on their own."
            elif i >= len(turns) - 3:
                instruction = "As a chemistry education assistant, the student has shown understanding of the concept. Help them summarize key points and confirm their understanding."
            else:
                instruction = "As a chemistry education assistant, based on the student's answer and previous dialogue history, continue using Socratic questioning to guide the student to think more deeply about this chemistry concept."
            
            # If there's dialogue history, add it to the current input
            if history:
                current_input = history + "Current student: " + student_text
            else:
                current_input = student_text
            
            # Create training instance
            training_instance = {
                "instruction": instruction,
                "input": current_input,
                "output": instructor_text
            }
            
            training_data.append(training_instance)
    
    return training_data

def batch_process_files(input_dir, output_dir):
    """Batch process all txt files in the directory"""
    
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process all txt files
    all_training_data = []
    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):
            file_path = os.path.join(input_dir, filename)
            
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # Parse dialogue
                training_data = parse_conversation_to_instructional_format(file_content)
                
                if training_data:
                    # Create a JSON file for each input file
                    output_filename = os.path.splitext(filename)[0] + '.json'
                    output_path = os.path.join(output_dir, output_filename)
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(training_data, f, ensure_ascii=False, indent=2)
                    
                    print(f"Processed {filename} and saved to {output_filename}")
                    
                    # Add data to the complete collection
                    all_training_data.extend(training_data)
                else:
                    print(f"Could not extract dialogue from {filename}")
            
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    # Save all training data to a single file
    combined_output_path = os.path.join(output_dir, 'all_training_data.json')
    with open(combined_output_path, 'w', encoding='utf-8') as f:
        json.dump(all_training_data, f, ensure_ascii=False, indent=2)
    
    # Create JSONL version (one JSON object per line, suitable for most training frameworks)
    jsonl_output_path = os.path.join(output_dir, 'all_training_data.jsonl')
    with open(jsonl_output_path, 'w', encoding='utf-8') as f:
        for instance in all_training_data:
            f.write(json.dumps(instance, ensure_ascii=False) + '\n')
    
    print(f"Processed a total of {len(all_training_data)} training instances")
    print(f"All data has been combined and saved to {combined_output_path} and {jsonl_output_path}")

# Set input and output directory paths
input_directory = r"./chemistry_educational_dialogs"  # Replace with your TXT files directory
output_directory = "./train_data/chemistry_educational_dialogs.json"  # Replace with your desired output directory for JSON files

# Execute batch processing
batch_process_files(input_directory, output_directory)
