from django.contrib import admin
from .models import Animal, EventoSanitario

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('nome', 'numero', 'data_nascimento', 'idade_meses', 'status')
    search_fields = ('nome', 'numero')
    list_filter = ('status',)

@admin.register(EventoSanitario)
class EventoSanitarioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'animal', 'tipo', 'data_prevista', 'realizado', 'data_realizada')
    list_filter = ('tipo', 'realizado', 'data_prevista')
    search_fields = ('titulo', 'animal__nome', 'animal__numero')