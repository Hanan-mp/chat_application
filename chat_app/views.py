from datetime import timedelta
from django.shortcuts import get_object_or_404, render,redirect,HttpResponse
from django.contrib.auth import authenticate, login as auth_login,logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from chat_app.models import ChatMessage, Thread
from django.contrib.auth.decorators import login_required

from chat_application import settings
from .forms import CreateThreadForm
from django.db.models import Q
from django.utils import timezone
from .models import PasswordReset, Profile
from django.core.mail import EmailMessage

@login_required(login_url='signup/')
def create_thread(request):
    user = request.user  # Logged-in user
    
    if request.method == 'POST':
        form = CreateThreadForm(request.POST, user=user)
        
        if form.is_valid():
            second_person = form.cleaned_data['second_person']
            
            # Check if the thread already exists
            existing_thread = Thread.objects.filter(
                (Q(first_person=user) & Q(second_person=second_person)) | 
                (Q(first_person=second_person) & Q(second_person=user))
            ).first()
            
            if existing_thread:
                # If a thread already exists, redirect to the chat page or show a message
                return redirect('chat')  # You could display a message here too
                
            # Create a new thread with a timestamp
            thread = Thread(
                first_person=user,
                second_person=second_person,
                timestamp=timezone.now(),  # Manually set the timestamp field
                updated=timezone.now()  # Set the updated field manually
            )
            thread.save()
            
            # Optionally, you can redirect to the newly created thread's chat
            return redirect('chat')  # Or you can redirect to the newly created thread's page
    
    else:
        form = CreateThreadForm(user=user)
    
    return render(request, 'chat/create_thread.html', {'form': form})





# def view_chat(request):
#     user = request.user

#     # Retrieve threads for the user and prefetch related messages
#     threads = Thread.objects.by_user(user=user).prefetch_related('chat_message_thread')
#     
#     # Add profile images for both users in each thread
#     for thread in threads:
#         # Get the profile image for both participants in the thread
#         thread.first_person_profile = Profile.objects.filter(user=thread.first_person).first()
#         thread.second_person_profile = Profile.objects.filter(user=thread.second_person).first()

#         # Get the latest message sent by the other user (not the logged-in user)
#         thread.latest_message = thread.chat_message_thread.exclude(
#             user=user  # Exclude messages sent by the logged-in user
#         ).order_by('-timestamp').first()  # Get the most recent message from the other user

#     context = {
#         'my_variable': threads,
#         'no_threads': threads.count() == 0,  # Add a flag for no threads
#         
#     }
#     return render(request, 'chat/chat.html', context)


@login_required(login_url='')
def view_chat(request, thread_id=None): 
    if request.user.is_authenticated:   
        user = request.user

        # Retrieve all threads for the user with prefetch_related to optimize database queries
        threads = Thread.objects.by_user(user=user).prefetch_related('chat_message_thread')
        user_profile = Profile.objects.get(user=user)

        # Add profile images and latest message for each thread
        for thread in threads:
            thread.first_person_profile = thread.first_person.profile
            thread.second_person_profile = thread.second_person.profile

            if thread.first_person == user:
                thread.sender_profile = thread.first_person_profile
                thread.receiver_profile = thread.second_person_profile
            else:
                thread.sender_profile = thread.second_person_profile
                thread.receiver_profile = thread.first_person_profile

            thread.latest_message = thread.chat_message_thread.exclude(user=user).order_by('-timestamp').first()

        # If a thread_id is provided, use it, otherwise, select the last thread
        if thread_id:
            active_thread = Thread.objects.filter(id=thread_id).first()
        else:
            active_thread = threads.last()  # Select the last thread if no thread_id is given

        # Check if the active_thread exists and that the user is part of it
        if active_thread and (active_thread.first_person == user or active_thread.second_person == user):
            active_thread.first_person_profile = active_thread.first_person.profile
            active_thread.second_person_profile = active_thread.second_person.profile

            if active_thread.first_person == user:
                active_thread.sender_profile = active_thread.first_person_profile
                active_thread.receiver_profile = active_thread.second_person_profile
            else:
                active_thread.sender_profile = active_thread.second_person_profile
                active_thread.receiver_profile = active_thread.first_person_profile

            active_thread.latest_message = active_thread.chat_message_thread.exclude(user=user).order_by('-timestamp').first()
        else:
            # If no valid active_thread is found, handle the error or fall back to the first thread
            active_thread = None

        # Pass all the chat messages and context to the template
        context = {
            'my_variable': threads,  # List of all threads for the user
            'active_thread': active_thread,  # The currently selected active thread
            'no_threads': len(threads) == 0,  # Whether there are no threads
            'user_profile': user_profile,  # User profile
        }

        return render(request, 'chat/chat.html', context)








@login_required(login_url='')
def mark_messages_as_read(request, thread_id):
    user = request.user
    
    # Get the thread by ID
    thread = get_object_or_404(Thread, id=thread_id)
    
    # Mark all messages in the thread from the other user as read
    chat_messages = ChatMessage.objects.filter(
        thread=thread,
        is_read=False
    ).exclude(user=user)  # Exclude messages sent by the logged-in user
    
    chat_messages.update(is_read=True)  # Mark these messages as read
    
    # Redirect to the chat view or to the thread's page
    return redirect('chat')  # Redirect back to the chat page


def login_view(request):
    if request.user.is_authenticated:
        return redirect('chat')
    if request.method == 'POST':
        username = request.POST.get("name")
        password = request.POST.get("password")
        
        if not username:
             error = "Username is required"
             return render(request, 'login/login.html', {'message': error,'username': username, 'password': password})
        
        if not password:
            error = "Password required"
            return render(request, 'login/login.html', {'message': error,'username': username, 'password': password})
        
        if len(password) < 8:
            error = "password must be Atleast 8 charecter"
            return render(request, 'login/login.html', {'message': error,'username': username, 'password': password})
        
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            print("Authentication successful")
            return redirect('chat')  # Use redirect for better practice
        else:
            messages.error(request, "Invalid credentials")

    return render(request, 'login/login.html')

def signup(request):
    if request.method == 'POST':
        # Extract data from POST request
        uname = request.POST.get('name')  # Get the username
        email = request.POST.get('email')  # Get the email
        pass1 = request.POST.get('password1')  # Get the password
        pass2 = request.POST.get('password2')  # Repeat password
        
        # Handle file upload for profile image
        profile_image = request.FILES.get('profile_image')  # Get the uploaded file
        
        # Validation for required fields
        if not uname:
            error = "Username required"
            return render(request, 'signup/signup.html', {'message': error, 'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})
        
        if not email:
            error = "Email field is required"
            return render(request, 'signup/signup.html', {'message': error, 'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})
        
        if '@' not in email:
            error = "Invalid email address. It must contain an '@' symbol"
            return render(request, 'signup/signup.html', {'message': error, 'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})
        
        if not pass1 or not pass2:
            error = "Password required"
            return render(request, 'signup/signup.html', {'message': error, 'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})
        
        if len(pass1) < 8:
            error = "password must be Atleast 8 charecter"
            return render(request, 'signup/signup.html', {'message': error,'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})
        
        # Check if passwords match
        if pass1 != pass2:
            error = "Passwords are not matching"
            return render(request, 'signup/signup.html', {'message': error, 'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})
        
        if User.objects.filter(username=uname).exists():
            error = "This username already exists"
            return render(request, 'signup/signup.html', {'message': error, 'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})
        
        if User.objects.filter(email=email).exists():
            error = "This email already exists"
            return render(request, 'signup/signup.html', {'message': error, 'username': uname, 'email': email, 'password1': pass1, 'password2': pass2})

        # Create the user
        try:
            user = User.objects.create_user(username=uname, password=pass1, email=email)
            user.save()

            # Create the profile and save the image (if provided)
            profile = Profile(user=user, profile_image=profile_image) if profile_image else Profile(user=user)
            profile.save()
            
            success = "User created successfully"
            return render(request, 'signup/signup.html', {'success': success})

            # return redirect('login')  # Redirect to the login page after successful registration
        except Exception as e:
            return HttpResponse(f"Error creating user: {str(e)}", status=400)

    return render(request, 'signup/signup.html')


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
    return redirect('login') 

def forgot_password(request):
   
    if request.method == 'POST':
        email = request.POST.get('email') 
            
        try:
            user = User.objects.get(email=email)
            new_password_reset = PasswordReset(user = user)
            new_password_reset.save()
            password_reset_url = reverse('change_password',kwargs={'reset_id':new_password_reset.reset_id})
            full_password_reset_url = f'{request.scheme}://{request.get_host()}{password_reset_url}'
            email_body = f'Reset your password using the link below:\n\n\n{full_password_reset_url}'
            
            email_message = EmailMessage(
                'Reset your password', #email subject
                email_body,
                settings.EMAIL_HOST_USER,#email sender
                [email] # receiver
            )
            
            email_message.fail_silently = True
            email_message.send()
        
            
            return redirect('password_reset_sent',reset_id=new_password_reset.reset_id)
        
                
        except User.DoesNotExist:
            error = f"No user with email '{email}' found."
            return render(request, 'forget/password_reset_form.html', {"message": error})
        except Exception:
            error = " you'r in poor connection.please try again"
            return render(request, 'forget/password_reset_form.html', {"message": error})
    return render(request, 'forget/password_reset_form.html')

def password_reset_sent(request,reset_id):
    if PasswordReset.objects.filter(reset_id=reset_id).exists():
        return render(request,'forget/password_reset_done.html')
    else:
        #redirect to forgot password page if code does not exist
        return redirect('forget_password')
    
def change_password(request,reset_id):
    try:
        password_reset_id = PasswordReset.objects.get(reset_id=reset_id)
        
        if request.method=="POST":
            password = request.POST.get('new_password1')
            confirm_password = request.POST.get('new_password2')
            
            password_have_error = False
            
            if not password:
                password_have_error = True
                error = "Password required"
                return render(request,'forget/password_reset_confirm.html',{"message":error})
            
            if len(password) < 8:
                password_have_error = True
                error = "password must be Atleast 8 charecter"
                return render(request,'forget/password_reset_confirm.html',{"message":error})
            
            if password != confirm_password:
                password_have_error = True
                error = "Password is not matching together"
                return render(request,'forget/password_reset_confirm.html',{"message":error})
            
            
            
            expiration_time = password_reset_id.created_when + timedelta(minutes=10)
            
            if timezone.now() > expiration_time:
                password_have_error = True
                error = "reset link has expired"
                password_reset_id.delete()
                return render(request,'forget/password_reset_confirm.html',{"message":error})
            
            if not password_have_error:
                user = password_reset_id.user
                user.set_password(password)
                user.save()
                
                #delete reset id after use
                password_reset_id.delete()
                
                return render(request,'forget/password_reset_complete.html')
            else:
                return redirect('change_password',reset_id=reset_id)
            
    except PasswordReset.DoesNotExist:
        return redirect('forget_password')
    
    return render(request,'forget/password_reset_confirm.html')