from django.urls import path
from . import views

app_name = 'saude'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('animais/', views.lista_animais_view, name='lista_animais'),
    path('perfil/', views.perfil_view, name='perfil'),
]