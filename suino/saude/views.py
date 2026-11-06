from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Animal, ESPECIE_CHOICES, ESPECIE_ICONES, EventoSanitario
from django.http import JsonResponse

@login_required
def home_view(request):
    return render(request, 'saude/home.html')

@login_required
def perfil_view(request):
    return render(request, 'saude/perfil.html')

@login_required
def lista_animais_view(request):
    especie = request.GET.get('especie', '')
    animais = Animal.objects.all()
    if especie in dict(ESPECIE_CHOICES):
        animais = animais.filter(especie=especie)

    especies = [
        {'valor': valor, 'rotulo': rotulo, 'icone': ESPECIE_ICONES[valor]}
        for valor, rotulo in ESPECIE_CHOICES
    ]
    context = {
        'animais': animais.order_by('-id'),
        'especies': especies,
        'especie_selecionada': especie,
    }
    return render(request, 'saude/lista_animais.html', context)

@login_required
def api_eventos_json(request):
    """API que retorna os eventos sanitários no formato aceito pelo FullCalendar"""
    animal_id = request.GET.get('animal_id')
    especie = request.GET.get('especie', '')
    eventos = EventoSanitario.objects.all()

    if especie in dict(ESPECIE_CHOICES):
        eventos = eventos.filter(animal__especie=especie)
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
            'title': f"#{ev.animal.numero}: {ev.titulo}",
            'start': ev.data_prevista.strftime('%Y-%m-%d'),
            'color': cor,
            'extendedProps': {
                'tipo': ev.get_tipo_display(),
                'animal': str(ev.animal),
                'especie': ev.animal.especie,
                'realizado': ev.realizado,
                'data_realizada': ev.data_realizada.strftime('%d/%m/%Y') if ev.data_realizada else 'Pendente'
            }
        })

    return JsonResponse(lista_eventos, safe=False)

@login_required
def calendario_view(request):
    animais = Animal.objects.all().order_by('especie', 'numero')
    especies = [
        {'valor': valor, 'rotulo': rotulo, 'icone': ESPECIE_ICONES[valor]}
        for valor, rotulo in ESPECIE_CHOICES
    ]
    context = {
        'animais': animais,
        'especies': especies,
    }
    return render(request, 'saude/calendario.html', context)