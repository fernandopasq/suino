from datetime import date, timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Animal, DoseVacina, EventoSanitario, PlanoVacina


class PerfilTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='usuario-perfil',
            password='senha-atual-123',
        )
        self.client.force_login(self.user)

    def test_perfil_exibe_formulario_colapsavel_de_troca_de_senha(self):
        response = self.client.get(reverse('saude:perfil'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Não informado')
        self.assertContains(response, 'name="first_name"')
        self.assertContains(response, 'name="last_name"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'Trocar senha')
        self.assertContains(response, 'data-bs-toggle="collapse"')
        self.assertContains(response, 'name="old_password"')
        self.assertContains(response, 'name="new_password1"')
        self.assertContains(response, 'name="new_password2"')

    def test_atualizar_informacoes_do_perfil(self):
        response = self.client.post(
            reverse('saude:perfil'),
            {
                'acao': 'atualizar_perfil',
                'first_name': 'Ana',
                'last_name': 'Silva',
                'email': 'ana@example.com',
            },
            follow=True,
        )

        self.user.refresh_from_db()
        self.assertRedirects(response, reverse('saude:perfil'))
        self.assertEqual(self.user.first_name, 'Ana')
        self.assertEqual(self.user.last_name, 'Silva')
        self.assertEqual(self.user.email, 'ana@example.com')
        self.assertContains(response, 'Seus dados de perfil foram atualizados.')
        self.assertContains(response, 'ana@example.com')

    def test_email_invalido_mantem_formulario_aberto_e_exibe_erro(self):
        response = self.client.post(
            reverse('saude:perfil'),
            {
                'acao': 'atualizar_perfil',
                'first_name': 'Ana',
                'last_name': 'Silva',
                'email': 'email-invalido',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="collapse show mt-3"')
        self.assertContains(response, 'Informe um endereço de e-mail válido.')
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, '')

    def test_troca_senha_exibe_feedback_e_mantem_usuario_logado(self):
        response = self.client.post(
            reverse('saude:perfil'),
            {
                'acao': 'alterar_senha',
                'old_password': 'senha-atual-123',
                'new_password1': 'Nova-senha-segura-948!',
                'new_password2': 'Nova-senha-segura-948!',
            },
            follow=True,
        )

        self.user.refresh_from_db()
        self.assertRedirects(response, reverse('saude:perfil'))
        self.assertTrue(self.user.check_password('Nova-senha-segura-948!'))
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertContains(response, 'Sua senha foi alterada com sucesso.')

    def test_troca_senha_invalida_mantem_formulario_aberto_e_exibe_erros(self):
        response = self.client.post(
            reverse('saude:perfil'),
            {
                'acao': 'alterar_senha',
                'old_password': 'senha-incorreta',
                'new_password1': 'Nova-senha-segura-948!',
                'new_password2': 'Nova-senha-segura-948!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="collapse show mt-3"')
        self.assertContains(response, 'A senha atual está incorreta.')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('senha-atual-123'))


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
            especie='galinaceo',
            numero='TESTE-GALINACEO',
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
        plano_galinaceos = PlanoVacina.objects.create(
            nome='Vacina para galináceos',
            especie='galinaceo',
            idade_primeira_dose_dias=7,
        )

        galinaceo = Animal.objects.create(
            especie='galinaceo',
            numero='TESTE-GALINACEO-002',
            data_nascimento=date(2026, 1, 1),
        )

        self.assertEqual(EventoSanitario.objects.filter(animal=galinaceo).count(), 1)
        self.assertTrue(EventoSanitario.objects.filter(animal=galinaceo, plano_vacina=plano_galinaceos).exists())
        self.assertFalse(EventoSanitario.objects.filter(animal=galinaceo, plano_vacina=plano_suinos).exists())

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
            janela_primeira_dose_dias=5,
        )
        DoseVacina.objects.create(plano_vacina=plano, numero=2, intervalo_dias=35, janela_dias=6)
        DoseVacina.objects.create(plano_vacina=plano, numero=3, intervalo_dias=14, janela_dias=8)
        DoseVacina.objects.create(plano_vacina=plano, numero=4, intervalo_dias=21, janela_dias=10)
        DoseVacina.objects.create(plano_vacina=plano, numero=5, intervalo_dias=7, janela_dias=12)

        eventos = EventoSanitario.objects.filter(
            animal=animal,
            plano_vacina=plano,
        ).order_by('dose_numero')

        self.assertEqual(
            [evento.data_prevista.isoformat() for evento in eventos],
            ['2026-01-08', '2026-02-12', '2026-02-26', '2026-03-19', '2026-03-26'],
        )
        self.assertEqual(
            [evento.janela_dias for evento in eventos],
            [5, 6, 8, 10, 12],
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
        self.assertEqual(evento.janela_dias, 7)

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
            especie='galinaceo',
            numero='TESTE-GALINACEO-FILTRO',
            data_nascimento='2026-01-01',
        )

        response = self.client.get(reverse('saude:lista_animais'), {'especie': 'galinaceo'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'gTESTE-GALINACEO-FILTRO')
        self.assertNotContains(response, 'sTESTE-SUINO-FILTRO')
        self.assertContains(response, '🐔')
        self.assertContains(response, 'Galináceo')

    def test_pagina_de_cadastro_exibe_campos_do_admin_com_bootstrap(self):
        response = self.client.get(reverse('saude:animal_cadastrar'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="especie"')
        self.assertContains(response, 'name="numero"')
        self.assertContains(response, 'name="data_nascimento"')
        self.assertContains(response, 'name="status"')
        self.assertContains(response, 'class="form-select"')
        self.assertContains(response, 'class="form-control"')

    def test_cadastro_cria_animal_e_gera_eventos_do_plano_da_especie(self):
        plano = PlanoVacina.objects.create(
            nome='Vacina para galináceos',
            especie='galinaceo',
            idade_primeira_dose_dias=7,
        )

        response = self.client.post(
            reverse('saude:animal_cadastrar'),
            {
                'especie': 'galinaceo',
                'numero': 'NOVO-001',
                'data_nascimento': '2026-01-01',
                'status': 'ativo',
            },
        )

        animal = Animal.objects.get(especie='galinaceo', numero='NOVO-001')
        self.assertRedirects(response, reverse('saude:lista_animais'))
        self.assertTrue(
            EventoSanitario.objects.filter(
                animal=animal,
                plano_vacina=plano,
                dose_numero=1,
            ).exists()
        )

    def test_cadastro_rejeita_numero_duplicado_na_mesma_especie(self):
        Animal.objects.create(
            especie='suino',
            numero='DUPLICADO-001',
            data_nascimento='2026-01-01',
        )

        response = self.client.post(
            reverse('saude:animal_cadastrar'),
            {
                'especie': 'suino',
                'numero': 'DUPLICADO-001',
                'data_nascimento': '2026-02-01',
                'status': 'ativo',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Animal with this Espécie and Número / Brinco already exists.')
        self.assertEqual(Animal.objects.filter(especie='suino', numero='DUPLICADO-001').count(), 1)

    def test_numero_pode_se_repetir_em_especies_diferentes_com_identificadores_distintos(self):
        suino = Animal.objects.create(
            especie='suino',
            numero='1',
            data_nascimento=date(2025, 1, 1),
        )
        galinaceo = Animal.objects.create(
            especie='galinaceo',
            numero='1',
            data_nascimento=date(2025, 1, 1),
        )

        self.assertEqual(suino.identificador, 's1')
        self.assertEqual(galinaceo.identificador, 'g1')
        self.assertNotEqual(suino.identificador, galinaceo.identificador)

    def test_numero_duplicado_na_mesma_especie_e_rejeitado(self):
        Animal.objects.create(
            especie='suino',
            numero='1',
            data_nascimento=date(2025, 1, 1),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Animal.objects.create(
                    especie='suino',
                    numero='1',
                    data_nascimento=date(2025, 1, 2),
                )

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
        self.assertContains(response, 'Bovino bTESTE-DETALHES')
        self.assertContains(response, 'Vacina aplicada')
        self.assertContains(response, 'Aplicada em 02/02/2025')
        self.assertContains(response, 'Próxima vacina')
        self.assertContains(response, 'Não aplicada')
        self.assertContains(response, 'Marcar aplicada')
        self.assertContains(response, 'Vermífugo')
        self.assertContains(response, 'Janela até')
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

    def test_aplicacao_fora_da_data_prevista_reagenda_doses_seguindo_intervalos(self):
        animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-REAGENDAMENTO',
            data_nascimento=date(2025, 1, 1),
        )
        plano = PlanoVacina.objects.create(
            nome='Vacina com reagendamento',
            especie='suino',
            idade_primeira_dose_dias=7,
        )
        DoseVacina.objects.create(plano_vacina=plano, numero=2, intervalo_dias=35)
        DoseVacina.objects.create(plano_vacina=plano, numero=3, intervalo_dias=14)
        DoseVacina.objects.create(plano_vacina=plano, numero=4, intervalo_dias=21)

        primeira_dose = EventoSanitario.objects.get(
            animal=animal,
            plano_vacina=plano,
            dose_numero=1,
        )
        segunda_dose = EventoSanitario.objects.get(
            animal=animal,
            plano_vacina=plano,
            dose_numero=2,
        )
        terceira_dose = EventoSanitario.objects.get(
            animal=animal,
            plano_vacina=plano,
            dose_numero=3,
        )
        quarta_dose = EventoSanitario.objects.get(
            animal=animal,
            plano_vacina=plano,
            dose_numero=4,
        )
        self.assertEqual(
            [segunda_dose.data_prevista, terceira_dose.data_prevista, quarta_dose.data_prevista],
            [date(2025, 2, 12), date(2025, 2, 26), date(2025, 3, 19)],
        )

        response = self.client.post(
            reverse('saude:animal_detalhe', args=[animal.pk]),
            {
                'acao': 'registrar_vacina',
                'evento_id': primeira_dose.pk,
                f'aplicacao-{primeira_dose.pk}-data_realizada': '2025-01-20',
            },
        )

        segunda_dose.refresh_from_db()
        terceira_dose.refresh_from_db()
        quarta_dose.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(segunda_dose.data_prevista, date(2025, 2, 24))
        self.assertEqual(terceira_dose.data_prevista, date(2025, 3, 10))
        self.assertEqual(quarta_dose.data_prevista, date(2025, 3, 31))

    def test_proxima_dose_usa_data_real_da_dose_anterior_aplicada(self):
        animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-DOSE-INTERMEDIARIA',
            data_nascimento=date(2025, 1, 1),
        )
        plano = PlanoVacina.objects.create(
            nome='Vacina com dose intermediária',
            especie='suino',
            idade_primeira_dose_dias=7,
        )
        DoseVacina.objects.create(plano_vacina=plano, numero=2, intervalo_dias=35)
        DoseVacina.objects.create(plano_vacina=plano, numero=3, intervalo_dias=14)

        primeira_dose = EventoSanitario.objects.get(
            animal=animal,
            plano_vacina=plano,
            dose_numero=1,
        )
        primeira_dose.realizado = True
        primeira_dose.data_realizada = date(2025, 1, 8)
        primeira_dose.save(update_fields=('realizado', 'data_realizada'))

        segunda_dose = EventoSanitario.objects.get(
            animal=animal,
            plano_vacina=plano,
            dose_numero=2,
        )
        terceira_dose = EventoSanitario.objects.get(
            animal=animal,
            plano_vacina=plano,
            dose_numero=3,
        )

        response = self.client.post(
            reverse('saude:animal_detalhe', args=[animal.pk]),
            {
                'acao': 'registrar_vacina',
                'evento_id': segunda_dose.pk,
                f'aplicacao-{segunda_dose.pk}-data_realizada': '2025-03-01',
            },
        )

        terceira_dose.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(terceira_dose.data_prevista, date(2025, 3, 15))

    def test_doses_adicionais_se_classificam_pela_previsao_e_sao_recalculadas_apos_aplicacao(self):
        hoje = date.today()
        animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-DOSES-DEPENDENTES',
            data_nascimento=hoje - timedelta(days=100),
        )
        plano = PlanoVacina.objects.create(
            nome='Vacina com doses dependentes',
            especie='suino',
            idade_primeira_dose_dias=7,
            janela_primeira_dose_dias=7,
        )
        DoseVacina.objects.create(
            plano_vacina=plano,
            numero=2,
            intervalo_dias=35,
            janela_dias=7,
        )
        DoseVacina.objects.create(
            plano_vacina=plano,
            numero=3,
            intervalo_dias=14,
            janela_dias=7,
        )

        primeira_dose = EventoSanitario.objects.get(
            animal=animal,
            plano_vacina=plano,
            dose_numero=1,
        )
        segunda_dose = EventoSanitario.objects.get(
            animal=animal,
            plano_vacina=plano,
            dose_numero=2,
        )
        terceira_dose = EventoSanitario.objects.get(
            animal=animal,
            plano_vacina=plano,
            dose_numero=3,
        )

        self.assertEqual(primeira_dose.status_vacina, 'Não aplicada')
        self.assertEqual(segunda_dose.status_vacina, 'Não aplicada')
        self.assertEqual(terceira_dose.status_vacina, 'Não aplicada')
        self.assertEqual(animal.status_sanitario_atual, 'Em dia')

        response = self.client.post(
            reverse('saude:animal_detalhe', args=[animal.pk]),
            {
                'acao': 'registrar_vacina',
                'evento_id': primeira_dose.pk,
                f'aplicacao-{primeira_dose.pk}-data_realizada': hoje.isoformat(),
            },
        )

        segunda_dose.refresh_from_db()
        terceira_dose.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(segunda_dose.data_prevista, hoje + timedelta(days=35))
        self.assertEqual(segunda_dose.status_vacina, 'Agendada')
        self.assertEqual(terceira_dose.data_prevista, hoje + timedelta(days=49))
        self.assertEqual(terceira_dose.status_vacina, 'Agendada')

        response = self.client.post(
            reverse('saude:animal_detalhe', args=[animal.pk]),
            {
                'acao': 'registrar_vacina',
                'evento_id': segunda_dose.pk,
                f'aplicacao-{segunda_dose.pk}-data_realizada': (hoje + timedelta(days=40)).isoformat(),
            },
        )

        terceira_dose.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(terceira_dose.data_prevista, hoje + timedelta(days=54))
        self.assertEqual(terceira_dose.status_vacina, 'Agendada')

    def test_dose_adicional_pendente_se_classifica_pela_data_prevista(self):
        animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-DOSE-SEM-ANTERIOR',
            data_nascimento=date(2025, 1, 1),
        )
        plano = PlanoVacina.objects.create(
            nome='Vacina sequencial',
            especie='suino',
            idade_primeira_dose_dias=7,
        )
        DoseVacina.objects.create(plano_vacina=plano, numero=2, intervalo_dias=35)
        segunda_dose = EventoSanitario.objects.get(
            animal=animal,
            plano_vacina=plano,
            dose_numero=2,
        )

        segunda_dose.data_prevista = date.today() - timedelta(days=1)
        segunda_dose.save(update_fields=('data_prevista',))

        self.assertEqual(segunda_dose.status_vacina, 'Pendente')
        response = self.client.get(
            reverse('saude:animal_detalhe', args=[animal.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pendente')
        self.assertNotContains(response, 'Aguardando dose anterior')

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

    def test_situacao_sanitaria_fica_pendente_somente_dentro_da_janela(self):
        animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-JANELA-STATUS',
            data_nascimento=date(2025, 1, 1),
        )
        EventoSanitario.objects.create(
            animal=animal,
            titulo='Vacina dentro da janela',
            tipo='vacina',
            data_prevista=date.today(),
            janela_dias=7,
        )

        self.assertEqual(animal.status_sanitario_atual, 'Pendente')

        EventoSanitario.objects.filter(animal=animal).update(
            data_prevista=date.today() - timedelta(days=7),
        )
        self.assertEqual(animal.status_sanitario_atual, 'Pendente')

        EventoSanitario.objects.filter(animal=animal).update(
            data_prevista=date.today() - timedelta(days=8),
        )
        self.assertEqual(animal.status_sanitario_atual, 'Em dia')

    def test_status_da_vacina_distingue_agendada_pendente_e_nao_aplicada(self):
        animal = Animal.objects.create(
            especie='suino',
            numero='TESTE-JANELA-VACINA',
            data_nascimento=date(2025, 1, 1),
        )
        evento = EventoSanitario.objects.create(
            animal=animal,
            titulo='Vacina com janela',
            tipo='vacina',
            data_prevista=date.today() + timedelta(days=1),
            janela_dias=7,
        )
        self.assertEqual(evento.status_vacina, 'Agendada')

        evento.data_prevista = date.today() - timedelta(days=7)
        self.assertEqual(evento.status_vacina, 'Pendente')
        self.assertEqual(evento.fim_janela_vacinacao, date.today())

        evento.data_prevista = date.today() - timedelta(days=8)
        self.assertEqual(evento.status_vacina, 'Não aplicada')

        evento.realizado = True
        self.assertEqual(evento.status_vacina, 'Aplicada')

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
            especie='galinaceo',
            numero='TESTE-CALENDARIO-INDIVIDUO',
            data_nascimento=date(2025, 1, 1),
        )

        response = self.client.get(
            reverse('saude:calendario'),
            {'animal_id': animal.pk, 'especie': 'suino'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['animal_selecionado'], animal)
        self.assertEqual(response.context['especie_selecionada'], 'galinaceo')
        self.assertContains(response, f'value="{animal.pk}" data-especie="galinaceo" selected')

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
        self.assertContains(response, 'janela_dias')
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
                'title': 'sTESTE-002: Vacina teste',
                'start': '2026-01-08',
                'color': '#0d6efd',
                'extendedProps': {
                    'tipo': 'Vacina',
                    'animal': 'Suíno (sTESTE-002)',
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
        galinaceo = Animal.objects.create(
            especie='galinaceo',
            numero='TESTE-GALINACEO',
            data_nascimento='2026-01-01',
        )
        EventoSanitario.objects.create(animal=suino, titulo='Tratamento', data_prevista='2026-01-08')
        EventoSanitario.objects.create(animal=galinaceo, titulo='Tratamento', data_prevista='2026-01-08')

        response = self.client.get(
            reverse('saude:api_eventos'),
            {'especie': 'galinaceo', 'animal_id': galinaceo.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['extendedProps']['especie'], 'galinaceo')
        self.assertEqual(response.json()[0]['extendedProps']['animal'], 'Galináceo (gTESTE-GALINACEO)')
