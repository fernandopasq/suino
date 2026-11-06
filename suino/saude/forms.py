from django import forms

from .models import Animal


class AnimalForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = ('especie', 'numero', 'data_nascimento', 'status')
        widgets = {
            'especie': forms.Select(attrs={'class': 'form-select'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'data_nascimento': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'},
            ),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class StatusAnimalForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = ('status',)
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class AplicacaoVacinaForm(forms.Form):
    data_realizada = forms.DateField(
        label="Data da aplicação",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )

    def __init__(self, *args, evento_id, **kwargs):
        super().__init__(*args, **kwargs)
        self.prefix = f"aplicacao-{evento_id}"
