from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Animal

@login_required
def home_view(request):
    return render(request, 'saude/home.html')

@login_required
def perfil_view(request):
    return render(request, 'saude/perfil.html')

@login_required
def lista_animais_view(request):
    animais = Animal.objects.all().order_by('-id')
    context = {
        'animais': animais
    }
    return render(request, 'saude/lista_animais.html', context)