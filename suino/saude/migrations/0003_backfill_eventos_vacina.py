from datetime import timedelta

from django.db import migrations


def gerar_eventos_existentes(apps, schema_editor):
    Animal = apps.get_model('saude', 'Animal')
    PlanoVacina = apps.get_model('saude', 'PlanoVacina')
    EventoSanitario = apps.get_model('saude', 'EventoSanitario')
    database = schema_editor.connection.alias

    animais = Animal.objects.using(database).all()
    planos = PlanoVacina.objects.using(database).all()

    for animal in animais.iterator():
        for plano in planos.iterator():
            data_primeira_dose = animal.data_nascimento + timedelta(
                days=plano.idade_recomendada_dias
            )

            for dose in range(1, plano.quantidade_doses + 1):
                data_prevista = data_primeira_dose + timedelta(
                    days=(dose - 1) * plano.intervalo_doses_dias
                )
                EventoSanitario.objects.using(database).get_or_create(
                    animal_id=animal.pk,
                    plano_vacina_id=plano.pk,
                    dose_numero=dose,
                    defaults={
                        'titulo': f'{plano.nome} ({dose}ª Dose)',
                        'tipo': 'vacina',
                        'data_prevista': data_prevista,
                        'realizado': False,
                    },
                )


class Migration(migrations.Migration):

    dependencies = [
        ('saude', '0002_planovacina_eventosanitario_dose_numero_and_more'),
    ]

    operations = [
        migrations.RunPython(gerar_eventos_existentes, migrations.RunPython.noop),
    ]
