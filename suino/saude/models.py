from django.db import models
from datetime import date

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
    def idade_meses(self):
        hoje = date.today()
        delta = hoje - self.data_nascimento
        return max(0, delta.days // 30)

    def __str__(self):
        return f"{self.nome} (#{self.numero})"


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

    def __str__(self):
        status_str = "Realizado" if self.realizado else "Pendente"
        return f"{self.titulo} - {self.animal.nome} ({status_str})"