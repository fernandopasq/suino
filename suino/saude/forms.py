from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm

from .models import Animal


class PerfilForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email')
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'email': 'E-mail',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Seu nome',
                'autocomplete': 'given-name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Seu sobrenome',
                'autocomplete': 'family-name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'voce@exemplo.com',
                'autocomplete': 'email',
            }),
        }
        help_texts = {
            'email': 'Opcional. Informe um e-mail válido para manter seus dados atualizados.',
        }
        error_messages = {
            'email': {
                'invalid': 'Informe um endereço de e-mail válido.',
            },
        }


class AlterarSenhaForm(PasswordChangeForm):
    error_messages = {
        **PasswordChangeForm.error_messages,
        'password_incorrect': 'A senha atual está incorreta. Tente novamente.',
        'password_mismatch': 'As senhas novas não coincidem.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = 'Senha atual'
        self.fields['new_password1'].label = 'Nova senha'
        self.fields['new_password1'].help_text = 'A senha deve ter pelo menos 8 caracteres.'
        self.fields['new_password2'].label = 'Confirme a nova senha'
        self.fields['new_password2'].help_text = 'Digite novamente a nova senha para confirmar.'
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


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
