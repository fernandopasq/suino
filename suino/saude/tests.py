from datetime import date, timedelta

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

    def test_lista_abre_pagina_de_detalhes_do_individuo(self):
        animal = Animal.objects.create(
            especie='bovino',
            numero='TESTE-DETALHE-LINK',
            data_nascimento=date(2025, 1, 1),
        )

        response = self.client.get(reverse('saude:lista_animais'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse('saude:animal_detalhe', args=[animal.pk]),
        )

    def test_detalhes_exibem_informacoes_vacinas_e_remedios(self):
        animal = Animal.objects.create(
            especie='bovino',
            numero='TESTE-DETALHES',
            data_nascimento=date(2025, 1, 1),
        )
        EventoSanitario.objects.create(
            animal=animal,
            titulo='Vacina aplicada',
            tipo='vacina',
            data_prevista=date(2025, 2, 1),
            realizado=True,
            data_realizada=date(2025, 2, 2),
        )
        EventoSanitario.objects.create(
            animal=animal,
            titulo='Próxima vacina',
            tipo='vacina',
            data_prevista=date(2025, 3, 1),
        )
        EventoSanitario.objects.create(
            animal=animal,
            titulo='Vermífugo',
            tipo='remedio',
            data_prevista=date(2025, 4, 1),
        )

        response = self.client.get(reverse('saude:animal_detalhe', args=[animal.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bovino #TESTE-DETALHES')
        self.assertContains(response, 'Vacina aplicada')
        self.assertContains(response, 'Aplicada em 02/02/2025')
        self.assertContains(response, 'Próxima vacina')
        self.assertContains(response, 'Marcar aplicada')
        self.assertContains(response, 'Vermífugo')
        self.assertContains(response, f'animal_id={animal.pk}')

    def test_registra_aplicacao_de_vacina_com_data(self):
        animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-APLICACAO',
            data_nascimento=date(2025, 1, 1),
        )
        evento = EventoSanitario.objects.create(
            animal=animal,
            titulo='Vacina aplicada agora',
            tipo='vacina',
            data_prevista=date(2025, 2, 1),
        )

        response = self.client.post(
            reverse('saude:animal_detalhe', args=[animal.pk]),
            {
                'acao': 'registrar_vacina',
                'evento_id': evento.pk,
                f'aplicacao-{evento.pk}-data_realizada': '2025-02-03',
            },
        )

        evento.refresh_from_db()
        self.assertRedirects(
            response,
            f"{reverse('saude:animal_detalhe', args=[animal.pk])}#vacinas",
            fetch_redirect_response=False,
        )
        self.assertTrue(evento.realizado)
        self.assertEqual(evento.data_realizada, date(2025, 2, 3))

    def test_data_invalida_na_aplicacao_nao_marca_vacina(self):
        animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-APLICACAO-INVALIDA',
            data_nascimento=date(2025, 1, 1),
        )
        evento = EventoSanitario.objects.create(
            animal=animal,
            titulo='Vacina pendente',
            tipo='vacina',
            data_prevista=date(2025, 2, 1),
        )

        response = self.client.post(
            reverse('saude:animal_detalhe', args=[animal.pk]),
            {
                'acao': 'registrar_vacina',
                'evento_id': evento.pk,
                f'aplicacao-{evento.pk}-data_realizada': 'data-invalida',
            },
        )

        evento.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(evento.realizado)
        self.assertContains(response, 'Enter a valid date.')

    def test_nao_permite_registrar_vacina_de_outro_animal(self):
        animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-ANIMAL-PRINCIPAL',
            data_nascimento=date(2025, 1, 1),
        )
        outro_animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-ANIMAL-OUTRO',
            data_nascimento=date(2025, 1, 1),
        )
        evento = EventoSanitario.objects.create(
            animal=outro_animal,
            titulo='Vacina privada',
            tipo='vacina',
            data_prevista=date(2025, 2, 1),
        )

        response = self.client.post(
            reverse('saude:animal_detalhe', args=[animal.pk]),
            {
                'acao': 'registrar_vacina',
                'evento_id': evento.pk,
                f'aplicacao-{evento.pk}-data_realizada': '2025-02-03',
            },
        )

        evento.refresh_from_db()
        self.assertEqual(response.status_code, 404)
        self.assertFalse(evento.realizado)

    def test_altera_status_para_obito_ou_abatido(self):
        animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-STATUS',
            data_nascimento=date(2025, 1, 1),
        )

        response = self.client.post(
            reverse('saude:animal_detalhe', args=[animal.pk]),
            {'acao': 'alterar_status', 'status': 'obito'},
        )

        animal.refresh_from_db()
        self.assertRedirects(response, reverse('saude:animal_detalhe', args=[animal.pk]))
        self.assertEqual(animal.status, 'obito')

    def test_status_manual_so_permite_ativo_abatido_ou_obito(self):
        animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-STATUS-CHOICES',
            data_nascimento=date(2025, 1, 1),
        )

        self.assertEqual(
            dict(Animal.STATUS_CHOICES),
            {'ativo': 'Ativo', 'abatido': 'Abatido', 'obito': 'Óbito'},
        )
        self.assertEqual(animal.status, 'ativo')

        response = self.client.post(
            reverse('saude:animal_detalhe', args=[animal.pk]),
            {'acao': 'alterar_status', 'status': 'pendente'},
        )

        animal.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(animal.status, 'ativo')
        self.assertContains(response, 'Select a valid choice')

    def test_situacao_sanitaria_e_calculada_para_animais_ativos(self):
        ativo_sem_pendencias = Animal.objects.create(
            especie='suino',
            numero='TESTE-ATIVO-EM-DIA',
            data_nascimento=date(2025, 1, 1),
        )
        ativo_pendente = Animal.objects.create(
            especie='suino',
            numero='TESTE-ATIVO-PENDENTE',
            data_nascimento=date(2025, 1, 1),
        )
        EventoSanitario.objects.create(
            animal=ativo_pendente,
            titulo='Vacina atrasada',
            tipo='vacina',
            data_prevista=date.today() - timedelta(days=1),
        )

        self.assertEqual(ativo_sem_pendencias.status_sanitario_atual, 'Em dia')
        self.assertEqual(ativo_pendente.status_sanitario_atual, 'Pendente')

    def test_animal_inativo_nao_recebe_situacao_pendente(self):
        for status in ('abatido', 'obito'):
            with self.subTest(status=status):
                animal = Animal.objects.create(
                    especie='suino',
                    numero=f'TESTE-INATIVO-{status}',
                    data_nascimento=date(2025, 1, 1),
                    status=status,
                )
                EventoSanitario.objects.create(
                    animal=animal,
                    titulo='Vacina vencida',
                    tipo='vacina',
                    data_prevista=date(2025, 2, 1),
                )

                self.assertEqual(
                    animal.status_sanitario_atual,
                    animal.get_status_display(),
                )

    def test_calendario_abre_com_individuo_e_especie_selecionados(self):
        animal = Animal.objects.create(
            especie='galinha',
            numero='TESTE-CALENDARIO-INDIVIDUO',
            data_nascimento=date(2025, 1, 1),
        )

        response = self.client.get(
            reverse('saude:calendario'),
            {'animal_id': animal.pk, 'especie': 'suino'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['animal_selecionado'], animal)
        self.assertEqual(response.context['especie_selecionada'], 'galinha')
        self.assertContains(response, f'value="{animal.pk}" data-especie="galinha" selected')

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
