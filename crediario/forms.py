# crediario/forms.py
from decimal import Decimal
from django import forms
from django.forms import inlineformset_factory
from django.db import transaction
from .models import Cliente, Nota, ItemNota, Pagamento

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        # campos existentes no model Cliente — ajuste se você tiver outros
        fields = ['nome', 'telefone', 'endereco', 'limite_crediario']

class NotaForm(forms.ModelForm):
    class Meta:
        model = Nota
        fields = ['cliente', 'numero_nota', 'data_nota', 'vencimento']

ItemFormSet = inlineformset_factory(
    Nota,
    ItemNota,
    fields=['descricao', 'quantidade', 'preco_unitario'],
    extra=1,
    can_delete=True,
)

class PagamentoForm(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = ['cliente', 'nota', 'valor_pagamento', 'metodo']