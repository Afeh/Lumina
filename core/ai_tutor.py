# core/ai_tutor.py
import google.generativeai as genai
from django.conf import settings
import json

# Configure the API client
genai.configure(api_key=settings.GOOGLE_API_KEY)
print(settings.GOOGLE_API_KEY)

# --- Define the model to use ---
# The older library versions used different model names. 
# 'text-bison-001' is the powerful text model from that era.
# Note: We don't create a model object here, we pass the name directly to the function.
model = genai.GenerativeModel('models/gemini-2.5-pro')  

# --- FUNCTION 1: Generate an Initial Evaluation Test ---
def generate_evaluation_test(num_questions=15):
    """
    Generates an initial set of questions.
    Returns a tuple: (data, error_message). On success, error_message is None.
    On failure, data is None.
    """
    prompt = f"""
    You are an expert WAEC English Language examiner for Nigerian students. 
    Your task is to generate a well-balanced, 15-question diagnostic test.
    The test must cover these three areas: Lexis and Structure, Comprehension, and Orals.

    Instructions:
    1. Create exactly {num_questions} multiple-choice questions (MCQs).
    2. Ensure a good mix of questions from Lexis & Structure (e.g., synonyms, antonyms, sentence completion), Comprehension (e.g., inference, main idea from a short passage), and Orals (e.g., identifying stress patterns, vowel sounds).
    3. For comprehension, include a short passage and base 2-3 questions on it.
    4. Provide four options (A, B, C, D) for each question.
    5. Clearly indicate the correct answer for each question.

    Return the output as a single, raw JSON object and nothing else. The object should have a key "questions" which is a list. Each item in the list should be a dictionary with the following keys: "question_text", "options" (a dictionary like {{"A": "text", "B": "text", ...}}), "correct_answer" (the letter, e.g., "C"), and "topic" (e.g., "Lexis", "Comprehension", "Orals").
    """
    try:
        # USE THE NEW SYNTAX
        response = model.generate_content(prompt)
        # AND USE .text
        json_response = response.text.replace('```json', '').replace('```', '').strip()
        
        # Add a check to see if the response is empty
        if not json_response:
            error_msg = "The AI returned an empty response."
            print(error_msg)
            return None, error_msg

        return json.loads(json_response), None # Success: return data and no error message

    except json.JSONDecodeError as e:
        error_msg = f"Failed to decode JSON from AI response. Error: {e}. Response was: {response.result}"
        print(error_msg)
        return None, "The AI returned a malformed response. Please try again."

    except Exception as e:
        # This will catch other errors like API key issues, network problems, etc.
        error_msg = f"An unexpected error occurred: {e}"
        print(error_msg)
        return None, "There was a problem connecting to the AI service. Please check your API key and try again."

# --- FUNCTION 2: Analyze Performance and Identify Weaknesses ---
def analyze_user_performance(user_answers):
    """
    Takes a list of questions, the user's answers, and correct answers, 
    then identifies specific weaknesses.
    """
    prompt = f"""
    You are an expert AI educational analyst for WAEC English.
    A Nigerian student has just completed a test. Here are the questions they got wrong:

    {json.dumps(user_answers, indent=2)}

    Based *only* on the questions they answered incorrectly, perform the following tasks:
    1.  **Identify Granular Weaknesses**: Pinpoint the specific skill gaps. Be very specific. Instead of "Grammar", say "Difficulty with subject-verb agreement" or "Trouble identifying correct stress in disyllabic words". List at least 3-5 specific weaknesses.
    2.  **Provide a Summary**: Write a brief, encouraging summary (2-3 sentences) of their performance, highlighting the key areas they need to focus on.

    Return your response as a JSON object with two keys: "weakness_summary" (a string) and "detailed_weaknesses" (a list of strings).
    """
    try:
        response = model.generate_content(prompt)
        json_response = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(json_response)
    except Exception as e:
        print(f"Error analyzing performance: {e}")
        return None


# --- FUNCTION 3: Explain a Wrong Answer ---
def get_bulk_explanations(wrong_answers):
    """
    Takes a list of all wrong answers and gets all explanations in a single API call.
    Returns a dictionary where keys are question texts and values are explanations.
    """
    prompt = f"""
    You are a patient and encouraging WAEC English Language tutor.
    A student answered several questions incorrectly. For each question in the list below, provide a clear, step-by-step explanation.

    LIST OF INCORRECT ANSWERS:
    {json.dumps(wrong_answers, indent=2)}

    Your task is to return a single, raw JSON object and absolutely nothing else. The keys of the object must be the exact "question_text" from the input, and the values should be the detailed explanation for that question.
    The explanation should:
    1. State the correct answer.
    2. Explain why it's correct.
    3. Explain why the user's chosen answer was incorrect.

    If you cannot provide an explanation for a specific question, use the value "Explanation could not be generated." for that key. Do not omit any keys.
    
    The entire output must be a single valid JSON object. Do not include ```json markdown wrappers or any other text.
    """
    try:
        response = model.generate_content(prompt)
        json_response = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(json_response)
    except Exception as e:
        print(f"Error getting bulk explanations: {e}")
        # On failure, create a dictionary with default failure messages
        # This prevents the results page from showing empty explanations
        failed_explanations = {}
        for answer in wrong_answers:
            failed_explanations[answer['question_text']] = "Sorry, the AI could not generate an explanation for this question at this time."
        return failed_explanations


# --- FUNCTION 4: Generate Personalized Practice Questions ---
def generate_personalized_quiz(weaknesses, num_questions=5):
    """
    Generates a new, targeted quiz based on identified weaknesses.
    """
    prompt = f"""
    You are an expert WAEC English Language question creator.
    A student needs to practice and has the following specific weaknesses:
    {', '.join(weaknesses)}

    Create a new, targeted practice quiz of {num_questions} multiple-choice questions.
    Each question should directly address one or more of the identified weaknesses.

    Return the output as a single JSON object, following the same format as the evaluation test: a key "questions" which is a list of question dictionaries.
    """
    try:
        response = model.generate_content(prompt)
        json_response = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(json_response)
    except Exception as e:
        print(f"Error generating personalized quiz: {e}")
        return None


# --- FUNCTION 5: General "Ask the Tutor" ---
def ask_tutor_question(user_question, chat_history=None):
    """
    Answers a general, free-form question from the user.
    """
    prompt = f"""
    You are 'Lumina', a friendly and knowledgeable AI English tutor for Nigerian students preparing for WAEC.
    A student has asked the following question:

    "{user_question}"

    Provide a clear, concise, and helpful answer. If the question is outside the scope of English Language, gently guide them back to the topic.
    """
    try:
        response = model.generate_content(prompt)
        return response.text 
    except Exception as e:
        print(f"Error in ask_tutor_question: {e}")
        return "I seem to be having trouble connecting right now. Please ask again in a moment."