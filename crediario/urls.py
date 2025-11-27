from django.urls import path
from . import views

app_name = 'crediario'

urlpatterns = [
    path('clientes/', views.clientes_list, name='clientes_list'),
    path('clientes/<int:pk>/', views.cliente_detail, name='cliente_detail'),
    path('notas/', views.nota_list, name='nota_list'),
    path('notas/<int:pk>/', views.nota_detail, name='nota_detail'),
    path('notas/novo/', views.nota_create, name='nota_create'),

    path('pagamentos/novo/', views.pagamento_create, name='pagamento_create'),
]