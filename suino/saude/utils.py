from datetime import timedelta

def gerar_eventos_vacinas_para_animal(animal):
    """Gera automaticamente os eventos sanitários de vacinação com base no plano de vacinas e na data de nascimento do animal."""
    from .models import PlanoVacina, EventoSanitario

    planos = PlanoVacina.objects.all()
    
    for plano in planos:
        # Calcula a data prevista para a primeira dose
        data_primeira_dose = animal.data_nascimento + timedelta(days=plano.idade_recomendada_dias)
        
        for dose in range(1, plano.quantidade_doses + 1):
            # Se for a partir da 2ª dose, soma o intervalo de dias proporcional
            dias_adicionais = (dose - 1) * plano.intervalo_doses_dias
            data_prevista_dose = data_primeira_dose + timedelta(days=dias_adicionais)
            
            titulo_dose = f"{plano.nome} ({dose}ª Dose)"
            
            # Verifica se já existe o evento gerado para evitar duplicidade
            EventoSanitario.objects.get_or_create(
                animal=animal,
                plano_vacina=plano,
                dose_numero=dose,
                defaults={
                    'titulo': titulo_dose,
                    'tipo': 'vacina',
                    'data_prevista': data_prevista_dose,
                    'realizado': False
                }
            )