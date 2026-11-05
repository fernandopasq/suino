from django.db import models
from datetime import date
from .utils import gerar_eventos_vacinas_para_animal

class Animal(models.Model):
    STATUS_CHOICES = [
        ('em_dia', 'Em dia'),
        ('pendente', 'Pendente'),
        ('abatido', 'Abatido'),
        ('obito', 'Óbito'),
    ]
    
    nome = models.CharField(max_length=100)
    numero = models.CharField(max_length=50, unique=True, verbose_name="Número / Brinco")
    data_nascimento = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='em_dia', verbose_name="Status de Saúde")
    foto = models.ImageField(upload_to='animais/', blank=True, null=True)
    
    @property
    def idade_dias(self):
        hoje = date.today()
        delta = hoje - self.data_nascimento
        return max(0, delta.days)

    @property
    def idade_meses(self):
        return self.idade_dias // 30

    def __str__(self):
        return f"{self.nome} (#{self.numero})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        # Se o animal foi recém-criado, gera o calendário de vacinas dele automaticamente
        if is_new:
            gerar_eventos_vacinas_para_animal(self)


class PlanoVacina(models.Model):
    """Catálogo de vacinas da granja com base na idade e doses"""
    nome = models.CharField(max_length=150, verbose_name="Nome da Vacina")
    descricao = models.TextField(blank=True, null=True, verbose_name="Descrição / Observações")
    idade_recomendada_dias = models.IntegerField(verbose_name="Idade para 1ª Dose (em dias)")
    quantidade_doses = models.IntegerField(default=1, verbose_name="Número total de doses")
    intervalo_doses_dias = models.IntegerField(default=0, verbose_name="Intervalo entre doses (em dias)")

    def __str__(self):
        return f"{self.nome} (1ª dose com {self.idade_recomendada_dias} dias)"


class EventoSanitario(models.Model):
    TIPO_CHOICES = [
        ('vacina', 'Vacina'),
        ('remedio', 'Remédio/Vermífugo'),
    ]
    
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='eventos', verbose_name="Animal")
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
        return f"{self.titulo} - {self.animal.nome} ({status_str})"