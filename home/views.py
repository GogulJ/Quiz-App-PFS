from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from .models import Quiz, Question, Answer, Marks_Of_User
from .forms import QuizForm, QuestionForm
from django.forms import inlineformset_factory
from io import BytesIO
from xhtml2pdf import pisa
from django.core.mail import send_mail
from .models import Marks_Of_User
from django.utils import timezone

# View to display all users (admin only)
@login_required
def admin_users(request):
    if not request.user.is_staff:
        return redirect('login')
    users = User.objects.all()
    return render(request, 'admin_users.html', {'users': users})

# View to display user profile
@login_required
def user_profile(request):
    return render(request, 'user_profile.html', {'user': request.user})

def send_mail_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user_marks = Marks_Of_User.objects.filter(user=user) 

    subject = "Your Quiz Results"
    message = f"Hello {user.username},\n\nHere are your quiz details:\n"
    for mark in user_marks:
        message += f"Quiz: {mark.quiz}\nScore: {mark.score}\n\n"
    message += f"\nTotal Marks: {sum(mark.score for mark in user_marks)}"

    send_mail(
        subject,
        message,
        'goguljeyaraj05@gmail.com',
        [user.email],
        fail_silently=False,
    )
    return HttpResponse("Email sent successfully.")

def generate_pdf_report(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    if request.user.is_staff:
        results = Marks_Of_User.objects.filter(quiz=quiz)
    else:
        results = Marks_Of_User.objects.filter(quiz=quiz, user=request.user)
    
    html_content = render_to_string('pdf_report.html', {
        'quiz': quiz,
        'results': results,
        'is_admin': request.user.is_staff
    })
    
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(html_content.encode('UTF-8')), pdf_file)
    
    if not pisa_status.err:
        response = HttpResponse(pdf_file.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="quiz_{quiz_id}_report.pdf"'
        return response
    else:
        return HttpResponse("Error generating PDF", status=500)
    
@login_required
def results(request):
    if request.user.is_staff:
        marks = Marks_Of_User.objects.all()  # Admin sees all marks
    else:
        marks = Marks_Of_User.objects.filter(user=request.user)  # User sees only their marks

    return render(request, "results.html", {'marks': marks})

def index(request):
    quiz = Quiz.objects.all()
    para = {'quiz': quiz}
    return render(request, "index.html", para)

@login_required(login_url='/login')
def quiz(request, myid):
    if request.user.is_staff:
        return redirect('view_report', quiz_id=myid)  
    quiz = Quiz.objects.get(id=myid)
    return render(request, "quiz.html", {'quiz': quiz})

def quiz_data_view(request, myid):
    quiz = Quiz.objects.get(id=myid)
    questions = []
    for q in quiz.get_questions():
        answers = [a.content for a in q.get_answers()]
        questions.append({str(q): answers})
    return JsonResponse({'data': questions, 'time': quiz.time})

def save_quiz_view(request, myid):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':  # AJAX check
        questions = []
        data = request.POST
        data_ = dict(data.lists())

        data_.pop('csrfmiddlewaretoken', None)

        for k in data_.keys():
            try:
                question = Question.objects.get(content=k)
                questions.append(question)
            except Question.DoesNotExist:
                return JsonResponse({'error': f'Question with content "{k}" not found'}, status=400)

        user = request.user
        try:
            quiz = Quiz.objects.get(id=myid)
        except Quiz.DoesNotExist:
            return JsonResponse({'error': 'Quiz not found'}, status=404)

        score = 0
        marks = []
        correct_answer = None

        for q in questions:
            a_selected = request.POST.get(q.content)

            if a_selected:  
                question_answers = Answer.objects.filter(question=q)
                for a in question_answers:
                    if a_selected == a.content:
                        if a.correct:
                            score += 1
                            correct_answer = a.content
                    else:
                        if a.correct:
                            correct_answer = a.content

                marks.append({str(q): {'correct_answer': correct_answer, 'answered': a_selected}})
            else:
                marks.append({str(q): 'not answered'})

        Marks_Of_User.objects.create(quiz=quiz, user=user, score=score, timestamp=timezone.now())

        return JsonResponse({'passed': True, 'score': score, 'marks': marks})
    else:
        return JsonResponse({'error': 'Invalid request method or not an AJAX request'}, status=400)

def Signup(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == "POST":   
        username = request.POST['username']
        email = request.POST['email']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        password = request.POST['password1']
        confirm_password = request.POST['password2']
        
        if password != confirm_password:
            return redirect('/register')
        
        user = User.objects.create_user(username, email, password)
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        return render(request, 'login.html')  
    return render(request, "signup.html")

def Login(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            return render(request, "login.html") 
    return render(request, "login.html")

def Logout(request):
    logout(request)
    return redirect('/')

def add_quiz(request):
    if request.method == "POST":
        form = QuizForm(data=request.POST)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.save()
            obj = form.instance
            return render(request, "add_quiz.html", {'obj': obj})
    else:
        form = QuizForm()
    return render(request, "add_quiz.html", {'form': form})

def add_question(request):
    questions = Question.objects.filter().order_by('-id')
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, "add_question.html")
    else:
        form = QuestionForm()
    return render(request, "add_question.html", {'form': form, 'questions': questions})

def delete_question(request, myid):
    question = Question.objects.get(id=myid)
    if request.method == "POST":
        question.delete()
        return redirect('/add_question')
    return render(request, "delete_question.html", {'question': question})

def add_options(request, myid):
    question = Question.objects.get(id=myid)
    QuestionFormSet = inlineformset_factory(Question, Answer, fields=('content', 'correct', 'question'), extra=4)
    if request.method == "POST":
        formset = QuestionFormSet(request.POST, instance=question)
        if formset.is_valid():
            formset.save()
            alert = True
            return render(request, "add_options.html", {'alert': alert})
    else:
        formset = QuestionFormSet(instance=question)
    return render(request, "add_options.html", {'formset': formset, 'question': question})

def delete_result(request, myid):
    marks = Marks_Of_User.objects.get(id=myid)
    if request.method == "POST":
        marks.delete()
        return redirect('/results')
    return render(request, "delete_result.html", {'marks': marks})