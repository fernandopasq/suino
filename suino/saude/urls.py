from django.urls import path
from . import views

app_name = 'saude'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('animais/', views.lista_animais_view, name='lista_animais'),
    path('animais/cadastrar/', views.animal_cadastrar_view, name='animal_cadastrar'),
    path('animais/<int:animal_id>/', views.animal_detalhe_view, name='animal_detalhe'),
    path('calendario/', views.calendario_view, name='calendario'),
    path('api/eventos/', views.api_eventos_json, name='api_eventos'),
    path('perfil/', views.perfil_view, name='perfil'),
]