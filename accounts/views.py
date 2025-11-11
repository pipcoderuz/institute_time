from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm


@login_required
def switch_role(request):
    if request.method == "POST":
        selected_role = request.POST.get("role")

        if selected_role and selected_role in request.user.roles:
            request.user.set_active_role(selected_role)
            messages.success(
                request, f"Active role changed to {selected_role}")
        else:
            messages.error(request, "Invalid role selected")

        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))



def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            if not user.roles:
                user.roles = ['student']
                user.save()
            if not user.active_role and user.roles:
                user.set_active_role('student')
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def user_logout(request):
    logout(request)
    return redirect('accounts:login')
