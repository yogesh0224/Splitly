from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import Group

def home(request):
    return render(request, 'billsplit/home.html')

@login_required
def dashboard(request):
    my_groups = Group.objects.filter(
        members__user=request.user,
        members__accepted=True
    ).order_by('-created_at')
    return render(request, 'billsplit/dashboard.html', {'groups': my_groups})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created! Welcome to Splitly 🎉")
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'billsplit/signup.html', {'form': form})