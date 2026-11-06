from django.db import migrations, models
import django.db.models.deletion


def migrar_doses_existentes(apps, schema_editor):
    PlanoVacina = apps.get_model('saude', 'PlanoVacina')
    DoseVacina = apps.get_model('saude', 'DoseVacina')
    database = schema_editor.connection.alias

    for plano in PlanoVacina.objects.using(database).all().iterator():
        quantidade = min(max(plano.quantidade_doses, 1), 5)
        intervalo = max(plano.intervalo_doses_dias, 0)
        for numero in range(2, quantidade + 1):
            DoseVacina.objects.using(database).create(
                plano_vacina_id=plano.pk,
                numero=numero,
                intervalo_dias=intervalo,
            )

    EventoSanitario = apps.get_model('saude', 'EventoSanitario')
    EventoSanitario.objects.using(database).filter(
        realizado=False,
        tipo='vacina',
        plano_vacina__isnull=False,
        dose_numero__gt=5,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('saude', '0006_alter_eventosanitario_animal'),
    ]

    operations = [
        migrations.RenameField(
            model_name='planovacina',
            old_name='idade_recomendada_dias',
            new_name='idade_primeira_dose_dias',
        ),
        migrations.AlterField(
            model_name='planovacina',
            name='idade_primeira_dose_dias',
            field=models.PositiveIntegerField(verbose_name='Idade para a 1ª dose (em dias)'),
        ),
        migrations.CreateModel(
            name='DoseVacina',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.PositiveSmallIntegerField(choices=[(2, '2ª dose'), (3, '3ª dose'), (4, '4ª dose'), (5, '5ª dose')], verbose_name='Dose')),
                ('intervalo_dias', models.PositiveIntegerField(verbose_name='Intervalo desde a dose anterior (em dias)')),
                ('plano_vacina', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='doses_adicionais', to='saude.planovacina', verbose_name='Plano de vacinação')),
            ],
            options={
                'ordering': ('numero',),
            },
        ),
        migrations.RunPython(migrar_doses_existentes, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='planovacina',
            name='quantidade_doses',
        ),
        migrations.RemoveField(
            model_name='planovacina',
            name='intervalo_doses_dias',
        ),
        migrations.AddConstraint(
            model_name='dosevacina',
            constraint=models.UniqueConstraint(fields=('plano_vacina', 'numero'), name='dose_unica_por_plano'),
        ),
        migrations.AddConstraint(
            model_name='dosevacina',
            constraint=models.CheckConstraint(condition=models.Q(('numero__gte', 2), ('numero__lte', 5)), name='dose_numero_entre_2_e_5'),
        ),
    ]
