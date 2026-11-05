from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Animal, EventoSanitario, PlanoVacina


class CalendarioSanitarioTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username='teste', password='senha-teste')
        self.client.force_login(user)

    def test_novo_plano_gera_eventos_para_animais_existentes(self):
        animal = Animal.objects.create(
            nome='Animal teste',
            numero='TESTE-001',
            data_nascimento='2026-01-01',
        )

        plano = PlanoVacina.objects.create(
            nome='Vacina teste',
            idade_recomendada_dias=7,
            quantidade_doses=2,
            intervalo_doses_dias=35,
        )

        eventos = EventoSanitario.objects.filter(animal=animal, plano_vacina=plano).order_by('dose_numero')

        self.assertEqual(eventos.count(), 2)
        self.assertEqual(eventos[0].data_prevista.isoformat(), '2026-01-08')
        self.assertEqual(eventos[1].data_prevista.isoformat(), '2026-02-12')

    def test_pagina_do_calendario_carrega_fullcalendar(self):
        response = self.client.get(reverse('saude:calendario'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'new FullCalendar.Calendar')

    def test_api_retorna_eventos_para_o_calendario(self):
        animal = Animal.objects.create(
            nome='Animal teste',
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
                'title': 'Animal teste: Vacina teste',
                'start': '2026-01-08',
                'color': '#0d6efd',
                'extendedProps': {
                    'tipo': 'Vacina',
                    'animal': 'Animal teste',
                    'realizado': False,
                    'data_realizada': 'Pendente',
                },
            }],
        )
