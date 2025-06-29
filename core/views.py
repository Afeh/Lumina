# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from django.utils import timezone
from datetime import timedelta
from . import ai_tutor
from .models import User, Question, Choice, EvaluationResult

import random

def landing_page(request):
    return render(request, 'landing.html')


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            login(request, user)
            # Redirect to the initial performance evaluation
            return redirect('start_evaluation') 
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/signup.html', {'form': form, 'page_title': 'Join Lumina'})

# --- NEW: login_view ---
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard') # Redirect if already logged in

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Here you can add logic for the login streak
                return redirect('dashboard') # Redirect to the main dashboard after login
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form, 'page_title': 'Welcome Back'})

#### Remember to add Login endpoint

# --- NEW: logout_view ---
@login_required
def logout_view(request):
    logout(request)
    return redirect('landing')

# --- PLACEHOLDER VIEWS (for URL routing to work) ---
# You will build these out later
@login_required
def dashboard_view(request):
    # This will be the user's main hub
    return render(request, 'dashboard.html')

@login_required
def start_evaluation_view(request):
    """
    Displays the introductory page for the evaluation test.
    """
    return render(request, 'evaluation/start.html')


@login_required
def take_evaluation_view(request):
    """
    Generates the test questions (if not already in session) and displays the test interface.
    """
    if request.method == 'POST':
        # This is triggered by clicking "Start Test" on the start page
        
        # 1. Call the AI to get questions
        test_data, error_message = ai_tutor.generate_evaluation_test() # Unpack the tuple

        # The condition is now much more explicit
        if error_message:
            # Handle AI error and show the message
            return render(request, 'evaluation/error.html', {'message': error_message})

        # Check for the questions key as a final safety measure
        if not test_data or 'questions' not in test_data:
            return render(request, 'evaluation/error.html', {'message': 'AI response was valid but missing the "questions" data.'})

        # 2. Store the test and start time in the user's session
        request.session['evaluation_questions'] = test_data['questions']
        request.session['evaluation_start_time'] = timezone.now().isoformat()
        
        # 3. Redirect to the same view with a GET request to show the test
        return redirect('take_evaluation')

    # ... (the rest of the view remains the same) ...
    # This is a GET request, so display the test
    questions = request.session.get('evaluation_questions')
    start_time_iso = request.session.get('evaluation_start_time')

    if not questions or not start_time_iso:
        # If the user tries to access this page directly without starting a test
        return redirect('start_evaluation')

    # Calculate deadline for the timer
    start_time = timezone.datetime.fromisoformat(start_time_iso)
    deadline = start_time + timedelta(minutes=15)
    
    context = {
        'questions': questions,
        'deadline_iso': deadline.isoformat()
    }
    return render(request, 'evaluation/take.html', context)


@login_required
def submit_evaluation_view(request):
    """
    Processes the submitted answers, calls the AI for analysis, saves the result, and redirects.
    """
    if request.method != 'POST':
        return redirect('start_evaluation')

    # 1. Retrieve the original questions from the session
    questions = request.session.get('evaluation_questions', [])
    if not questions:
        return redirect('start_evaluation') # Session expired or invalid access

    # 2. Process answers and calculate score
    score = 0
    points_change = 0
    wrong_answers_for_ai = []
    full_results_data = []

    for i, q in enumerate(questions):
        question_name = f"question_{i}" # Use the correct name format
        user_answer = request.POST.get(question_name)
        is_correct = (user_answer == q['correct_answer'])

        if is_correct:
            score += 1
            points_change += 10
        else:
            points_change -= 5
            # This list will be sent to the AI
            wrong_answers_for_ai.append({
                'question_text': q['question_text'],
                'options': q['options'],
                'user_answer': user_answer,
                'correct_answer': q['correct_answer']
            })
        
        full_results_data.append({
            'question_text': q['question_text'],
            'options': q['options'],
            'topic': q['topic'],
            'user_answer': user_answer,
            'correct_answer': q['correct_answer'],
            'is_correct': is_correct,
            'explanation': '' # Default empty explanation
        })

    # 3. Get AI analysis and explanations
    # Call 1: Get weakness analysis
    analysis = ai_tutor.analyze_user_performance(wrong_answers_for_ai)
    if not analysis: # Handle failure gracefully
        analysis = {'weakness_summary': 'Analysis could not be generated.', 'detailed_weaknesses': []}

    # Call 2: Get all explanations in one go
    all_explanations = ai_tutor.get_bulk_explanations(wrong_answers_for_ai)

    # Now, merge the explanations back into our results data
    for result_item in full_results_data:
        if not result_item['is_correct']:
            # Look up the explanation from the dictionary we received
            explanation_text = all_explanations.get(result_item['question_text'], "Sorry, an explanation could not be generated for this question.")
            result_item['explanation'] = explanation_text
    
    # --- Step 4 & 5: Update user points and save result ---
    user = request.user
    user.points += points_change
    user.save()

    result = EvaluationResult.objects.create(
        user=user,
        score=score,
        total_questions=len(questions),
        weakness_summary=analysis.get('weakness_summary'),
        detailed_weaknesses=analysis.get('detailed_weaknesses'),
        full_results_data=full_results_data
    )

    # --- Step 6 & 7: Clean up and redirect ---
    del request.session['evaluation_questions']
    del request.session['evaluation_start_time']

    return redirect('evaluation_results', result_id=result.id)


@login_required
def evaluation_results_view(request, result_id):
    """
    Displays the detailed results of a completed evaluation.
    """
    try:
        result = EvaluationResult.objects.get(id=result_id, user=request.user)
    except EvaluationResult.DoesNotExist:
        # Handle case where result doesn't exist or doesn't belong to the user
        return redirect('dashboard') 

    context = {
        'result': result
    }
    return render(request, 'evaluation/results.html', context)