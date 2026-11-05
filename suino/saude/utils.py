from datetime import timedelta

def _gerar_eventos_para_animal_e_plano(animal, plano):
    from .models import EventoSanitario

    data_primeira_dose = animal.data_nascimento + timedelta(days=plano.idade_recomendada_dias)

    for dose in range(1, plano.quantidade_doses + 1):
        dias_adicionais = (dose - 1) * plano.intervalo_doses_dias
        data_prevista_dose = data_primeira_dose + timedelta(days=dias_adicionais)
        titulo_dose = f"{plano.nome} ({dose}ª Dose)"

        EventoSanitario.objects.get_or_create(
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


def gerar_eventos_vacinas_para_animal(animal):
    """Gera os eventos de vacinação do animal com base nos planos cadastrados."""
    from .models import PlanoVacina

    for plano in PlanoVacina.objects.all():
        _gerar_eventos_para_animal_e_plano(animal, plano)


def gerar_eventos_vacinas_para_plano(plano):
    """Gera os eventos de um novo plano para todos os animais existentes."""
    from .models import Animal

    for animal in Animal.objects.all():
        _gerar_eventos_para_animal_e_plano(animal, plano)