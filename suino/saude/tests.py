from datetime import date

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Animal, DoseVacina, EventoSanitario, PlanoVacina


class CalendarioSanitarioTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username='teste', password='senha-teste')
        self.client.force_login(user)

    def test_novo_plano_gera_eventos_para_animais_existentes(self):
        animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-001',
            data_nascimento='2026-01-01',
        )

        plano = PlanoVacina.objects.create(
            nome='Vacina teste',
            especie='suino',
            idade_primeira_dose_dias=7,
        )
        DoseVacina.objects.create(
            plano_vacina=plano,
            numero=2,
            intervalo_dias=35,
        )

        eventos = EventoSanitario.objects.filter(animal=animal, plano_vacina=plano).order_by('dose_numero')

        self.assertEqual(eventos.count(), 2)
        self.assertEqual(eventos[0].data_prevista.isoformat(), '2026-01-08')
        self.assertEqual(eventos[1].data_prevista.isoformat(), '2026-02-12')

    def test_plano_gera_eventos_apenas_para_animais_da_especie(self):
        suino = Animal.objects.create(
            especie='suino',
            numero='TESTE-SUINO',
            data_nascimento='2026-01-01',
        )
        Animal.objects.create(
            especie='galinha',
            numero='TESTE-GALINHA',
            data_nascimento='2026-01-01',
        )

        plano = PlanoVacina.objects.create(
            nome='Vacina para suínos',
            especie='suino',
            idade_primeira_dose_dias=7,
        )

        self.assertEqual(
            EventoSanitario.objects.filter(plano_vacina=plano, animal=suino).count(),
            1,
        )
        self.assertEqual(EventoSanitario.objects.filter(plano_vacina=plano).count(), 1)

    def test_novo_animal_recebe_apenas_planos_da_sua_especie(self):
        plano_suinos = PlanoVacina.objects.create(
            nome='Vacina para suínos',
            especie='suino',
            idade_primeira_dose_dias=7,
        )
        plano_galinhas = PlanoVacina.objects.create(
            nome='Vacina para galinhas',
            especie='galinha',
            idade_primeira_dose_dias=7,
        )

        galinha = Animal.objects.create(
            especie='galinha',
            numero='TESTE-GALINHA-002',
            data_nascimento=date(2026, 1, 1),
        )

        self.assertEqual(EventoSanitario.objects.filter(animal=galinha).count(), 1)
        self.assertTrue(EventoSanitario.objects.filter(animal=galinha, plano_vacina=plano_galinhas).exists())
        self.assertFalse(EventoSanitario.objects.filter(animal=galinha, plano_vacina=plano_suinos).exists())

    def test_doses_individuais_usam_intervalos_a_partir_da_dose_anterior(self):
        animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-DOSES-001',
            data_nascimento=date(2026, 1, 1),
        )
        plano = PlanoVacina.objects.create(
            nome='Vacina com intervalos variáveis',
            especie='suino',
            idade_primeira_dose_dias=7,
        )
        DoseVacina.objects.create(plano_vacina=plano, numero=2, intervalo_dias=35)
        DoseVacina.objects.create(plano_vacina=plano, numero=3, intervalo_dias=14)
        DoseVacina.objects.create(plano_vacina=plano, numero=4, intervalo_dias=21)
        DoseVacina.objects.create(plano_vacina=plano, numero=5, intervalo_dias=7)

        eventos = EventoSanitario.objects.filter(
            animal=animal,
            plano_vacina=plano,
        ).order_by('dose_numero')

        self.assertEqual(
            [evento.data_prevista.isoformat() for evento in eventos],
            ['2026-01-08', '2026-02-12', '2026-02-26', '2026-03-19', '2026-03-26'],
        )

    def test_editar_intervalo_recalcula_eventos_pendentes_e_remover_dose_os_exclui(self):
        animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-DOSES-002',
            data_nascimento=date(2026, 1, 1),
        )
        plano = PlanoVacina.objects.create(
            nome='Vacina editável',
            especie='suino',
            idade_primeira_dose_dias=7,
        )
        dose = DoseVacina.objects.create(plano_vacina=plano, numero=2, intervalo_dias=35)

        dose.intervalo_dias = 40
        dose.save()
        evento = EventoSanitario.objects.get(animal=animal, plano_vacina=plano, dose_numero=2)
        self.assertEqual(evento.data_prevista.isoformat(), '2026-02-17')

        dose.delete()
        self.assertFalse(
            EventoSanitario.objects.filter(animal=animal, plano_vacina=plano, dose_numero=2).exists()
        )

    def test_gestao_de_animais_filtra_por_especie(self):
        Animal.objects.create(
            especie='suino',
            numero='TESTE-SUINO-FILTRO',
            data_nascimento='2026-01-01',
        )
        Animal.objects.create(
            especie='galinha',
            numero='TESTE-GALINHA-FILTRO',
            data_nascimento='2026-01-01',
        )

        response = self.client.get(reverse('saude:lista_animais'), {'especie': 'galinha'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '#TESTE-GALINHA-FILTRO')
        self.assertNotContains(response, '#TESTE-SUINO-FILTRO')
        self.assertContains(response, '🐔')

    def test_pagina_do_calendario_carrega_fullcalendar(self):
        response = self.client.get(reverse('saude:calendario'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'new FullCalendar.Calendar')

    def test_admin_permite_adicionar_doses_extras_ao_plano(self):
        admin = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='senha-admin',
        )
        self.client.force_login(admin)

        response = self.client.get(reverse('admin:saude_planovacina_add'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Doses adicionais (até a 5ª dose)')
        self.assertContains(response, 'intervalo_dias')
        self.assertContains(response, 'Add another Dose adicional')
        self.assertContains(response, 'empty-form')

    def test_api_retorna_eventos_para_o_calendario(self):
        animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-002',
            data_nascimento='2026-01-01',
        )
        evento = EventoSanitario.objects.create(
            animal=animal,
            titulo='Vacina teste',
            data_prevista='2026-01-08',
        )

        response = self.client.get(reverse('saude:api_eventos'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [{
                'id': evento.id,
                'title': '#TESTE-002: Vacina teste',
                'start': '2026-01-08',
                'color': '#0d6efd',
                'extendedProps': {
                    'tipo': 'Vacina',
                    'animal': 'Suíno (#TESTE-002)',
                    'especie': 'suino',
                    'realizado': False,
                    'data_realizada': 'Pendente',
                },
            }],
        )

    def test_api_filtra_eventos_por_especie_e_numero_do_animal(self):
        suino = Animal.objects.create(
            especie='suino',
            numero='TESTE-SUINO',
            data_nascimento='2026-01-01',
        )
        galinha = Animal.objects.create(
            especie='galinha',
            numero='TESTE-GALINHA',
            data_nascimento='2026-01-01',
        )
        EventoSanitario.objects.create(animal=suino, titulo='Tratamento', data_prevista='2026-01-08')
        EventoSanitario.objects.create(animal=galinha, titulo='Tratamento', data_prevista='2026-01-08')

        response = self.client.get(
            reverse('saude:api_eventos'),
            {'especie': 'galinha', 'animal_id': galinha.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['extendedProps']['especie'], 'galinha')
        self.assertEqual(response.json()[0]['extendedProps']['animal'], 'Galinha (#TESTE-GALINHA)')
