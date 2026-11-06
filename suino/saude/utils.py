from datetime import timedelta

def _gerar_eventos_para_animal_e_plano(animal, plano):
    from .models import EventoSanitario

    dose_intervals = [(1, 0, plano.janela_primeira_dose_dias)] + [
        (dose.numero, dose.intervalo_dias, dose.janela_dias)
        for dose in plano.doses_adicionais.all()
    ]
    dose_numeros = [numero for numero, _, _ in dose_intervals]
    eventos_existentes = {
        evento.dose_numero: evento
        for evento in EventoSanitario.objects.filter(
            animal=animal,
            plano_vacina=plano,
            dose_numero__isnull=False,
        )
    }
    eventos_pendentes = EventoSanitario.objects.filter(
        animal=animal,
        plano_vacina=plano,
        realizado=False,
        dose_numero__isnull=False,
    )
    if dose_numeros:
        eventos_pendentes.exclude(dose_numero__in=dose_numeros).delete()

    data_base = animal.data_nascimento + timedelta(days=plano.idade_primeira_dose_dias)
    for dose, intervalo_dias, janela_dias in dose_intervals:
        if dose > 1:
            data_prevista_dose = data_base + timedelta(days=intervalo_dias)
        else:
            data_prevista_dose = data_base

        titulo_dose = f"{plano.nome} ({dose}ª Dose)"
        evento = eventos_existentes.get(dose)
        if evento is None:
            evento = EventoSanitario.objects.create(
                animal=animal,
                plano_vacina=plano,
                dose_numero=dose,
                titulo=titulo_dose,
                tipo='vacina',
                data_prevista=data_prevista_dose,
                janela_dias=janela_dias,
                realizado=False,
            )
            eventos_existentes[dose] = evento
        elif not evento.realizado:
            evento.titulo = titulo_dose
            evento.data_prevista = data_prevista_dose
            evento.janela_dias = janela_dias
            evento.save(update_fields=('titulo', 'data_prevista', 'janela_dias'))

        if evento.realizado and evento.data_realizada:
            data_base = evento.data_realizada
        else:
            data_base = data_prevista_dose


def recalcular_eventos_vacinas_para_animal_e_plano(animal, plano):
    """Reagenda as doses futuras usando a data real das doses já aplicadas."""
    _gerar_eventos_para_animal_e_plano(animal, plano)


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