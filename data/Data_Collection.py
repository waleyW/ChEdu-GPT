import os
import openai
import json
import time
from dotenv import load_dotenv
import random

# Load environment variables from .env file
load_dotenv(r'GPT_api/api.env')

# Verify if the API key is loaded correctly
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("API key not found. Please ensure the .env file is correct and the key is properly set.")

# Set API key from environment variable
openai.api_key = api_key

def gpt4o_generate_dialog(prompt, model="gpt-4o", max_tokens=2000, temperature=0.7):
    """Generate a chemistry dialog using GPT-4o"""
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

def create_chemistry_prompt(topic, concept, level):
    """Create a prompt for generating a chemistry dialog"""
    return f"""
Generate a Socratic teaching dialog between a chemistry instructor and a student on the following topic:

TOPIC: {topic}
CONCEPT: {concept}
STUDENT LEVEL: {level}

DIALOG REQUIREMENTS:
1. Begin with the student expressing confusion or asking a question about the concept
2. The instructor should use guiding questions rather than direct explanations
3. Each instructor question should lead the student to think one level deeper
4. Include at least one instance of student misconception and instructor's guiding correction
5. Show gradual development of student's understanding
6. End with the student demonstrating deeper comprehension
7. Include 7-10 exchanges total

ADDITIONAL REQUIREMENTS:
- Use proper chemistry terminology and equations/formulas where appropriate
- Include metacognitive questions (like "How did you arrive at that conclusion?")
- Guide the student from specific examples to general principles
- Keep the dialog natural and realistic
- For advanced concepts, ensure explanations remain technically accurate

Format as:
Instructor: [question or response]
Student: [answer or question]
Instructor: [next guiding question]
...

Make sure the dialog represents authentic chemistry education and Socratic teaching methods.
"""

def generate_diverse_datasets(output_directory, num_dialogs=300):
    """Generate diverse chemistry dialog datasets"""
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    # Chemistry topics and concepts matrix
    topics_and_concepts = {
        "Thermodynamics": [
            "Gibbs Free Energy and Spontaneity", 
            "Enthalpy vs Entropy", 
            "Chemical Equilibrium Shifts", 
            "Phase Diagrams", 
            "Reaction Spontaneity Prediction"
        ],
        "Kinetics": [
            "Rate Determining Step", 
            "Reaction Order Determination", 
            "Arrhenius Equation", 
            "Reaction Mechanisms", 
            "Catalysts and Activation Energy"
        ],
        "Quantum Chemistry": [
            "Orbital Hybridization", 
            "Molecular Orbital Theory", 
            "Quantum Numbers", 
            "Heisenberg Uncertainty Principle", 
            "Electron Configuration"
        ],
        "Organic Chemistry": [
            "Nucleophilic Substitution Mechanisms", 
            "Stereochemistry and Chirality", 
            "Elimination Reactions", 
            "Aromatic Substitution Regioselectivity", 
            "Carbonyl Chemistry"
        ],
        "Analytical Chemistry": [
            "Spectroscopy Interpretation", 
            "Chromatography Techniques", 
            "Titration Curves", 
            "Electrochemical Cells", 
            "Buffer Solutions"
        ],
        "Inorganic Chemistry": [
            "Coordination Complexes", 
            "Crystal Field Theory", 
            "Periodic Trends", 
            "Acid-Base Theories", 
            "Organometallic Chemistry"
        ],
        "Biochemistry": [
            "Enzyme Kinetics", 
            "Protein Structure", 
            "Metabolic Pathways", 
            "DNA Replication", 
            "Lipid Bilayers"
        ],
        "Physical Chemistry": [
            "Gas Laws", 
            "Colligative Properties", 
            "Surface Chemistry", 
            "Statistical Thermodynamics", 
            "Electrochemistry"
        ]
    }
    
    levels = ["Beginner", "Intermediate", "Advanced"]
    
    # Create a list of all possible combinations
    combinations = []
    for topic, concepts in topics_and_concepts.items():
        for concept in concepts:
            for level in levels:
                combinations.append({
                    "topic": topic,
                    "concept": concept,
                    "level": level
                })
    
    # Shuffle to ensure diversity if we don't generate all combinations
    random.shuffle(combinations)
    
    # Select the required number of combinations
    selected_combinations = combinations[:num_dialogs]
    
    # Generate dialogs for each selected combination
    all_dialogs = []
    for i, combo in enumerate(selected_combinations):
        print(f"Generating dialog {i+1}/{num_dialogs}: {combo['topic']} - {combo['concept']} ({combo['level']})")
        
        prompt = create_chemistry_prompt(combo['topic'], combo['concept'], combo['level'])
        dialog = gpt4o_generate_dialog(prompt)
        
        if dialog:
            dialog_data = {
                "id": i+1,
                "topic": combo['topic'],
                "concept": combo['concept'],
                "level": combo['level'],
                "dialog": dialog
            }
            all_dialogs.append(dialog_data)
            
            # Save individual dialog file
            filename = f"dialog_{i+1:03d}_{combo['topic'].replace(' ', '_')}_{combo['level']}.txt"
            file_path = os.path.join(output_directory, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(dialog)
            
            print(f"Saved dialog to {file_path}")
            
            # To avoid API rate limits
            time.sleep(1)
        else:
            print(f"Failed to generate dialog for {combo['topic']} - {combo['concept']}")
    
    # Save complete dataset as JSON
    json_path = os.path.join(output_directory, "chemistry_educational_dialogs.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(all_dialogs, f, ensure_ascii=False, indent=2)
    
    print(f"Complete dataset saved to {json_path}")

if __name__ == "__main__":
    output_directory = r"./chemistry_educational_dialogs"
    
    # Generate 300 dialogs (adjust the number as needed)
    generate_diverse_datasets(output_directory, num_dialogs=300)
    
    print("Dialog generation completed!")
