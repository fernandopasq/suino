from django.db import migrations, models


def rename_species_value(apps, schema_editor):
    Animal = apps.get_model('saude', 'Animal')
    PlanoVacina = apps.get_model('saude', 'PlanoVacina')
    Animal.objects.filter(especie='galinha').update(especie='galinaceo')
    PlanoVacina.objects.filter(especie='galinha').update(especie='galinaceo')


def restore_species_value(apps, schema_editor):
    Animal = apps.get_model('saude', 'Animal')
    PlanoVacina = apps.get_model('saude', 'PlanoVacina')
    Animal.objects.filter(especie='galinaceo').update(especie='galinha')
    PlanoVacina.objects.filter(especie='galinaceo').update(especie='galinha')


class Migration(migrations.Migration):

    dependencies = [
        ('saude', '0010_dosevacina_janela_dias_eventosanitario_janela_dias_and_more'),
    ]

    operations = [
        migrations.RunPython(rename_species_value, restore_species_value),
        migrations.AlterField(
            model_name='animal',
            name='especie',
            field=models.CharField(
                choices=[
                    ('suino', 'Suíno'),
                    ('galinaceo', 'Galináceo'),
                    ('bovino', 'Bovino'),
                    ('ovino', 'Ovino'),
                    ('caprino', 'Caprino'),
                    ('equino', 'Equino'),
                    ('outro', 'Outro'),
                ],
                max_length=20,
                verbose_name='Espécie',
            ),
        ),
        migrations.AlterField(
            model_name='planovacina',
            name='especie',
            field=models.CharField(
                choices=[
                    ('suino', 'Suíno'),
                    ('galinaceo', 'Galináceo'),
                    ('bovino', 'Bovino'),
                    ('ovino', 'Ovino'),
                    ('caprino', 'Caprino'),
                    ('equino', 'Equino'),
                    ('outro', 'Outro'),
                ],
                max_length=20,
                verbose_name='Espécie',
            ),
        ),
    ]
