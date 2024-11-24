from django.urls import path
from . import views
from .views import generate_pdf_report
from django.contrib.auth.decorators import login_required, user_passes_test

# Helper function to restrict access to admin/staff users only
admin_required = user_passes_test(lambda u: u.is_staff, login_url='/login')

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:myid>/", login_required(views.quiz), name="quiz"),
    path('<int:myid>/data/', login_required(views.quiz_data_view), name='quiz-data'),
    path('<int:myid>/save/', login_required(views.save_quiz_view), name='quiz-save'),

    path("signup/", views.Signup, name="signup"),
    path("login/", views.Login, name="login"),
    path("logout/", views.Logout, name="logout"),

    # Admin-only views
    path('add_quiz/', admin_required(views.add_quiz), name='add_quiz'),    
    path('add_question/', admin_required(views.add_question), name='add_question'),  
    path('add_options/<int:myid>/', admin_required(views.add_options), name='add_options'), 
    path('delete_question/<int:myid>/', admin_required(views.delete_question), name='delete_question'),  
    path('delete_result/<int:myid>/', admin_required(views.delete_result), name='delete_result'),

    # Result views
    path('results/', login_required(views.results), name='results'),    
    path('generate_pdf_report/<int:quiz_id>/', login_required(generate_pdf_report), name='generate_pdf_report'),
    path('send_mail/<int:user_id>/', views.send_mail_view, name='send_mail'),
    path('quiz/<int:myid>/', views.quiz, name='quiz'),
    path('report/<int:quiz_id>/', views.generate_pdf_report, name='view_report'),

    path('users/', views.admin_users, name='admin_users'),
    path('user/profile/', views.user_profile, name='user_profile'),

]
