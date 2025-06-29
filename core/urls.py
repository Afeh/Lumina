from django.urls import path
from .views import (
    landing_page, 
    signup_view, 
    login_view, 
    logout_view,
    dashboard_view,
    start_evaluation_view,
	take_evaluation_view,
	submit_evaluation_view,
	evaluation_results_view,
	start_practice_view,
    take_practice_view,
    submit_practice_view,

)

urlpatterns = [
    path('', landing_page, name='landing'),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # Placeholder URLs for the rest of the app
    path('dashboard/', dashboard_view, name='dashboard'),
    path('evaluation/start/', start_evaluation_view, name='start_evaluation'),
    # path('leaderboard/', your_leaderboard_view, name='leaderboard'), # Add when ready
	path('evaluation/take/', take_evaluation_view, name='take_evaluation'),
    path('evaluation/submit/', submit_evaluation_view, name='submit_evaluation'),
    path('evaluation/results/<int:result_id>/', evaluation_results_view, name='evaluation_results'),
	path('practice/start/<int:result_id>/', start_practice_view, name='start_practice'),
    path('practice/take/', take_practice_view, name='take_practice'),
    path('practice/submit/', submit_practice_view, name='submit_practice'),
]