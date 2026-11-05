from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home_view(request):
    return render(request, 'saude/home.html')

@login_required
def perfil_view(request):
    return render(request, 'saude/perfil.html')