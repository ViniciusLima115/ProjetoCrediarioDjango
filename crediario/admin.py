from django.contrib import admin
from .models import Cliente, Nota, ItemNota, Pagamento, Anexo, Notificacao

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'telefone', 'limite_crediario', 'saldo_devedor')
    search_fields = ('nome', 'telefone')

@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'data_nota', 'vencimento', 'total', 'status')
    list_filter = ('status',)
    search_fields = ('cliente__nome', 'numero_nota')

@admin.register(ItemNota)
class ItemNotaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nota', 'descricao', 'quantidade', 'preco_unitario', 'subtotal')

@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'nota', 'valor_pagamento', 'data_pagamento')

@admin.register(Anexo)
class AnexoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nota', 'arquivo', 'criado_em')

@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo', 'cliente', 'nota', 'status', 'data_agendada', 'enviado_em')
    list_filter = ('status', 'tipo')