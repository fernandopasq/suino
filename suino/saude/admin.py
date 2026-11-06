from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from .models import Animal, DoseVacina, PlanoVacina, EventoSanitario
from .utils import gerar_eventos_vacinas_para_plano

admin.site.site_header = "Vettora | Administração"
admin.site.site_title = "Vettora"
admin.site.index_title = "Gestão sanitária de animais"

@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    list_display = ('especie', 'numero', 'data_nascimento', 'idade_dias', 'status_sanitario_atual')
    search_fields = ('numero', 'especie')
    list_filter = ('especie', 'status')

class DoseVacinaInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        numeros = [
            form.cleaned_data['numero']
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False)
        ]
        numeros.sort()
        doses_esperadas = list(range(2, 2 + len(numeros)))
        if numeros != doses_esperadas:
            raise ValidationError(
                "As doses adicionais devem ser cadastradas em sequência, começando pela 2ª dose."
            )


class DoseVacinaInline(admin.TabularInline):
    model = DoseVacina
    formset = DoseVacinaInlineFormSet
    fields = ('numero', 'intervalo_dias')
    extra = 0
    max_num = 4
    verbose_name = "dose adicional"
    verbose_name_plural = "Doses adicionais (até a 5ª dose)"


@admin.register(PlanoVacina)
class PlanoVacinaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'especie', 'idade_primeira_dose_dias')
    search_fields = ('nome',)
    list_filter = ('especie',)
    inlines = [DoseVacinaInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        gerar_eventos_vacinas_para_plano(form.instance)

@admin.register(EventoSanitario)
class EventoSanitarioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'animal', 'tipo', 'data_prevista', 'realizado', 'data_realizada')
    list_filter = ('tipo', 'animal__especie', 'realizado', 'data_prevista')
    search_fields = ('titulo', 'animal__numero', 'animal__especie')