from datetime import timedelta

def _gerar_eventos_para_animal_e_plano(animal, plano):
    from .models import EventoSanitario

    data_dose = animal.data_nascimento + timedelta(days=plano.idade_primeira_dose_dias)
    doses = [(1, data_dose)]

    for dose_adicional in plano.doses_adicionais.all():
        data_dose += timedelta(days=dose_adicional.intervalo_dias)
        doses.append((dose_adicional.numero, data_dose))

    dose_numeros = [numero for numero, _ in doses]
    eventos_pendentes = EventoSanitario.objects.filter(
        animal=animal,
        plano_vacina=plano,
        realizado=False,
        dose_numero__isnull=False,
    )
    if dose_numeros:
        eventos_pendentes.exclude(dose_numero__in=dose_numeros).delete()

    for dose, data_prevista_dose in doses:
        titulo_dose = f"{plano.nome} ({dose}ª Dose)"

        evento, criado = EventoSanitario.objects.get_or_create(
            animal=animal,
            plano_vacina=plano,
            dose_numero=dose,
            defaults={
                'titulo': titulo_dose,
                'tipo': 'vacina',
                'data_prevista': data_prevista_dose,
                'realizado': False,
            },
        )
        if not criado and not evento.realizado:
            evento.titulo = titulo_dose
            evento.data_prevista = data_prevista_dose
            evento.save(update_fields=('titulo', 'data_prevista'))


def gerar_eventos_vacinas_para_animal(animal):
    """Gera os eventos de vacinação do animal com base nos planos cadastrados."""
    from .models import PlanoVacina

    for plano in PlanoVacina.objects.filter(especie=animal.especie):
        _gerar_eventos_para_animal_e_plano(animal, plano)


def gerar_eventos_vacinas_para_plano(plano):
    """Gera os eventos de um novo plano para todos os animais existentes."""
    from .models import Animal

    for animal in Animal.objects.filter(especie=plano.especie):
        _gerar_eventos_para_animal_e_plano(animal, plano)