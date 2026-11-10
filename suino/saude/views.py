from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils import timezone

from .models import Animal, ESPECIE_CHOICES, ESPECIE_ICONES, EventoSanitario
from .forms import AlterarSenhaForm, AnimalForm, AplicacaoVacinaForm, PerfilForm, StatusAnimalForm

@login_required
def home_view(request):
    return render(request, 'saude/home.html')

@login_required
def perfil_view(request):
    perfil_form = PerfilForm(instance=request.user)
    senha_form = AlterarSenhaForm(request.user)
    mostrar_formulario_perfil = False
    mostrar_formulario_senha = False

    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'atualizar_perfil':
            mostrar_formulario_perfil = True
            perfil_form = PerfilForm(request.POST, instance=request.user)
            if perfil_form.is_valid():
                perfil_form.save()
                messages.success(request, "Seus dados de perfil foram atualizados.")
                return redirect('saude:perfil')
        elif acao == 'alterar_senha':
            mostrar_formulario_senha = True
            senha_form = AlterarSenhaForm(request.user, request.POST)
            if senha_form.is_valid():
                senha_form.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Sua senha foi alterada com sucesso.")
                return redirect('saude:perfil')
        else:
            return HttpResponseBadRequest("Ação de perfil inválida.")

    return render(request, 'saude/perfil.html', {
        'form_perfil': perfil_form,
        'form_senha': senha_form,
        'mostrar_formulario_perfil': mostrar_formulario_perfil,
        'mostrar_formulario_senha': mostrar_formulario_senha,
    })

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
def animal_cadastrar_view(request):
    form = AnimalForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        animal = form.save()
        messages.success(request, f"Animal {animal.identificador} cadastrado com sucesso.")
        return redirect('saude:lista_animais')

    return render(request, 'saude/animal_form.html', {'form': form})


@login_required
def animal_detalhe_view(request, animal_id):
    animal = get_object_or_404(Animal, pk=animal_id)
    status_form = StatusAnimalForm(instance=animal)
    aplicacao_form = None
    evento_form_id = None

    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'alterar_status':
            status_form = StatusAnimalForm(request.POST, instance=animal)
            if status_form.is_valid():
                status_form.save()
                messages.success(request, "Status do animal atualizado.")
                return redirect('saude:animal_detalhe', animal_id=animal.pk)
        elif acao == 'registrar_vacina':
            evento_id = request.POST.get('evento_id', '')
            if not evento_id.isdigit():
                return HttpResponseBadRequest("Identificador de vacina inválido.")
            evento = get_object_or_404(
                EventoSanitario,
                pk=evento_id,
                animal=animal,
                tipo='vacina',
            )
            if evento.realizado:
                messages.warning(request, "Essa vacina já foi registrada como aplicada.")
                return redirect(f"{reverse('saude:animal_detalhe', args=[animal.pk])}#vacinas")

            aplicacao_form = AplicacaoVacinaForm(request.POST, evento_id=evento.pk)
            evento_form_id = evento.pk
            if aplicacao_form.is_valid():
                with transaction.atomic():
                    evento.realizado = True
                    evento.data_realizada = aplicacao_form.cleaned_data['data_realizada']
                    evento.save(update_fields=('realizado', 'data_realizada'))

                    if evento.plano_vacina and evento.dose_numero is not None:
                        from .utils import recalcular_eventos_vacinas_para_animal_e_plano

                        recalcular_eventos_vacinas_para_animal_e_plano(
                            animal,
                            evento.plano_vacina,
                        )
                messages.success(request, f"A aplicação de “{evento.titulo}” foi registrada.")
                return redirect(f"{reverse('saude:animal_detalhe', args=[animal.pk])}#vacinas")
        else:
            return HttpResponseBadRequest("Ação inválida.")

    eventos_vacinas = animal.eventos.filter(tipo='vacina').select_related('plano_vacina').order_by(
        'data_prevista',
        'dose_numero',
    )
    vacinas = [
        {
            'evento': evento,
            'form': (
                aplicacao_form
                if evento.pk == evento_form_id
                else AplicacaoVacinaForm(
                    initial={'data_realizada': timezone.localdate()},
                    evento_id=evento.pk,
                )
            ) if not evento.realizado else None,
        }
        for evento in eventos_vacinas
    ]
    remedios = animal.eventos.filter(tipo='remedio').order_by('-data_prevista')

    return render(request, 'saude/animal_detalhe.html', {
        'animal': animal,
        'status_form': status_form,
        'vacinas': vacinas,
        'remedios': remedios,
        'aplicacao_form': aplicacao_form,
        'evento_form_id': evento_form_id,
    })


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
            'title': f"{ev.animal.identificador}: {ev.titulo}",
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
    especie_selecionada = request.GET.get('especie', '')
    if especie_selecionada not in dict(ESPECIE_CHOICES):
        especie_selecionada = ''

    animal_selecionado = None
    animal_id = request.GET.get('animal_id')
    if animal_id and animal_id.isdigit():
        animal_selecionado = Animal.objects.filter(pk=animal_id).first()
        if animal_selecionado:
            especie_selecionada = animal_selecionado.especie

    especies = [
        {'valor': valor, 'rotulo': rotulo, 'icone': ESPECIE_ICONES[valor]}
        for valor, rotulo in ESPECIE_CHOICES
    ]
    context = {
        'animais': animais,
        'especies': especies,
        'especie_selecionada': especie_selecionada,
        'animal_selecionado': animal_selecionado,
    }
    return render(request, 'saude/calendario.html', context)