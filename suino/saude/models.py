from django.db import models
from datetime import date
from .utils import gerar_eventos_vacinas_para_animal

ESPECIE_CHOICES = [
    ('suino', 'Suíno'),
    ('galinha', 'Galinha'),
    ('bovino', 'Bovino'),
    ('ovino', 'Ovino'),
    ('caprino', 'Caprino'),
    ('equino', 'Equino'),
    ('outro', 'Outro'),
]

ESPECIE_ICONES = {
    'suino': '🐖',
    'galinha': '🐔',
    'bovino': '🐄',
    'ovino': '🐑',
    'caprino': '🐐',
    'equino': '🐎',
    'outro': '🐾',
}


class Animal(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('abatido', 'Abatido'),
        ('obito', 'Óbito'),
    ]

    especie = models.CharField(max_length=20, choices=ESPECIE_CHOICES, verbose_name="Espécie")
    numero = models.CharField(max_length=50, unique=True, verbose_name="Número / Brinco")
    data_nascimento = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ativo', verbose_name="Status do Animal")

    @property
    def icone_especie(self):
        return ESPECIE_ICONES.get(self.especie, '🐾')

    @property
    def idade_dias(self):
        hoje = date.today()
        delta = hoje - self.data_nascimento
        return max(0, delta.days)

    @property
    def idade_meses(self):
        return self.idade_dias // 30

    @property
    def status_sanitario_atual(self):
        if self.status != 'ativo':
            return self.get_status_display()

        hoje = date.today()
        tem_pendencia = self.eventos.filter(
            tipo='vacina',
            realizado=False,
            data_prevista__lt=hoje,
        ).exists()
        return "Pendente" if tem_pendencia else "Em dia"

    def __str__(self):
        return f"{self.get_especie_display()} (#{self.numero})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        # Se o animal foi recém-criado, gera o calendário de vacinas dele automaticamente
        if is_new:
            gerar_eventos_vacinas_para_animal(self)


class PlanoVacina(models.Model):
    """Catálogo de vacinas da granja com base na idade e doses"""
    nome = models.CharField(max_length=150, verbose_name="Nome da Vacina")
    especie = models.CharField(max_length=20, choices=ESPECIE_CHOICES, verbose_name="Espécie")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição / Observações")
    idade_primeira_dose_dias = models.PositiveIntegerField(
        verbose_name="Idade para a 1ª dose (em dias)",
    )

    def __str__(self):
        return f"{self.nome} - {self.get_especie_display()} (1ª dose com {self.idade_primeira_dose_dias} dias)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from .utils import gerar_eventos_vacinas_para_plano

        gerar_eventos_vacinas_para_plano(self)


class DoseVacina(models.Model):
    NUMERO_CHOICES = [(numero, f"{numero}ª dose") for numero in range(2, 6)]

    plano_vacina = models.ForeignKey(
        PlanoVacina,
        on_delete=models.CASCADE,
        related_name='doses_adicionais',
        verbose_name="Plano de vacinação",
    )
    numero = models.PositiveSmallIntegerField(
        choices=NUMERO_CHOICES,
        verbose_name="Dose",
    )
    intervalo_dias = models.PositiveIntegerField(
        verbose_name="Intervalo desde a dose anterior (em dias)",
    )

    class Meta:
        ordering = ('numero',)
        constraints = [
            models.UniqueConstraint(
                fields=('plano_vacina', 'numero'),
                name='dose_unica_por_plano',
            ),
            models.CheckConstraint(
                condition=models.Q(numero__gte=2, numero__lte=5),
                name='dose_numero_entre_2_e_5',
            ),
        ]

    def __str__(self):
        return f"{self.numero}ª dose: aguardar {self.intervalo_dias} dias"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from .utils import gerar_eventos_vacinas_para_plano

        gerar_eventos_vacinas_para_plano(self.plano_vacina)

    def delete(self, *args, **kwargs):
        plano_vacina = self.plano_vacina
        result = super().delete(*args, **kwargs)
        from .utils import gerar_eventos_vacinas_para_plano

        gerar_eventos_vacinas_para_plano(plano_vacina)
        return result


class EventoSanitario(models.Model):
    TIPO_CHOICES = [
        ('vacina', 'Vacina'),
        ('remedio', 'Remédio/Vermífugo'),
    ]
    
    animal = models.ForeignKey(
        Animal,
        on_delete=models.CASCADE,
        related_name='eventos',
        verbose_name="Animal (espécie e número)",
    )
    titulo = models.CharField(max_length=150, verbose_name="Título / Descrição")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='vacina', verbose_name="Tipo")
    data_prevista = models.DateField(verbose_name="Data Prevista")
    realizado = models.BooleanField(default=False, verbose_name="Realizado?")
    data_realizada = models.DateField(blank=True, null=True, verbose_name="Data Realizada")

    # Referência opcional caso tenha vindo do plano automático
    plano_vacina = models.ForeignKey(PlanoVacina, on_delete=models.SET_NULL, blank=True, null=True, related_name='eventos_gerados')
    dose_numero = models.IntegerField(blank=True, null=True, verbose_name="Número da Dose")

    def __str__(self):
        status_str = "Realizado" if self.realizado else "Pendente"
        return f"{self.titulo} - {self.animal} ({status_str})"