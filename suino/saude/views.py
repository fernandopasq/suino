from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Animal, EventoSanitario
from django.http import JsonResponse

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

@login_required
def api_eventos_json(request):
    """API que retorna os eventos sanitários no formato aceito pelo FullCalendar"""
    animal_id = request.GET.get('animal_id')
    eventos = EventoSanitario.objects.all()

    if animal_id:
        eventos = eventos.filter(animal_id=animal_id)

    lista_eventos = []
    for ev in eventos:
        if ev.realizado:
            cor = '#198754' # Verde (Concluído)
        elif ev.tipo == 'vacina':
            cor = '#0d6efd' # Azul (Vacina pendente)
        else:
            cor = '#ffc107' # Amarelo/Laranja (Remédio pendente)

        lista_eventos.append({
            'id': ev.id,
            'title': f"{ev.animal.nome}: {ev.titulo}",
            'start': ev.data_prevista.strftime('%Y-%m-%d'),
            'color': cor,
            'extendedProps': {
                'tipo': ev.get_tipo_display(),
                'animal': ev.animal.nome,
                'realizado': ev.realizado,
                'data_realizada': ev.data_realizada.strftime('%d/%m/%Y') if ev.data_realizada else 'Pendente'
            }
        })

    return JsonResponse(lista_eventos, safe=False)

@login_required
def calendario_view(request):
    animais = Animal.objects.all().order_by('nome')
    context = {
        'animais': animais
    }
    return render(request, 'saude/calendario.html', context)