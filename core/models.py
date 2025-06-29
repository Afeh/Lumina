# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """Extends the default User model."""
    NIGERIAN_STATES = [
        ('AB', 'Abia'),
        ('AD', 'Adamawa'),
        ('AK', 'Akwa Ibom'),
        ('AN', 'Anambra'),
        ('BA', 'Bauchi'),
        ('BY', 'Bayelsa'),
        ('BE', 'Benue'),
        ('BO', 'Borno'),
        ('CR', 'Cross River'),
        ('DE', 'Delta'),
        ('EB', 'Ebonyi'),
        ('ED', 'Edo'),
        ('EK', 'Ekiti'),
        ('EN', 'Enugu'),
        ('FC', 'Federal Capital Territory (FCT)'),
        ('GO', 'Gombe'),
        ('IM', 'Imo'),
        ('JI', 'Jigawa'),
        ('KD', 'Kaduna'),
        ('KN', 'Kano'),
        ('KT', 'Katsina'),
        ('KE', 'Kebbi'),
        ('KO', 'Kogi'),
        ('KW', 'Kwara'),
        ('LA', 'Lagos'),
        ('NA', 'Nasarawa'),
        ('NI', 'Niger'),
        ('OG', 'Ogun'),
        ('ON', 'Ondo'),
        ('OS', 'Osun'),
        ('OY', 'Oyo'),
        ('PL', 'Plateau'),
        ('RI', 'Rivers'),
        ('SO', 'Sokoto'),
        ('TA', 'Taraba'),
        ('YO', 'Yobe'),
        ('ZA', 'Zamfara'),
    ]

    school_name = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(
        max_length=100,
        choices=NIGERIAN_STATES,
        blank=True,
        null=True,
        verbose_name="State"
    )
    points = models.IntegerField(default=0)
    last_login_streak_check = models.DateField(auto_now_add=True)
    login_streak = models.IntegerField(default=0)
    # Add login streak fields if you implement that feature

    def __str__(self):
        return self.username

class Question(models.Model):
    SUBJECT_CHOICES = [
        ('LEXIS_STRUCTURE', 'Lexis and Structure'),
        ('COMPREHENSION', 'Comprehension'),
        ('ORALS', 'Orals'),
        ('GENERAL', 'General'),
    ]
    
    subject_area = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    text = models.TextField()
    # For comprehension, you might have a passage.
    passage = models.TextField(blank=True, null=True)
    # You could also normalize this into a separate Passage model

    def __str__(self):
        return f"{self.get_subject_area_display()} - {self.text[:50]}..."

class Choice(models.Model):
    """Multiple choice options for a question."""
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text

class EvaluationResult(models.Model):
    """
    Stores the complete result of a single AI-powered evaluation test for a user.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evaluation_results')
    timestamp = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField()
    total_questions = models.IntegerField()

    # Store the AI's analysis directly
    weakness_summary = models.TextField(help_text="The AI's brief summary of performance.")
    detailed_weaknesses = models.JSONField(help_text="A list of specific weaknesses identified by the AI.")
    
    # Store the entire test context for review
    # This is powerful: it holds the questions, options, user's answers, and correct answers.
    full_results_data = models.JSONField(help_text="A JSON blob of the questions, user answers, and explanations.")

    class Meta:
        ordering = ['-timestamp'] # Show the most recent results first

    def __str__(self):
        return f"Evaluation for {self.user.username} on {self.timestamp.strftime('%Y-%m-%d')}"
    

