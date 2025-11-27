from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.contrib import messages
from .models import Cliente, Nota, ItemNota, Pagamento, Anexo
from .forms import ClienteForm, NotaForm, ItemFormSet, PagamentoForm

# --- Clientes ---
def clientes_list(request):
    clientes = Cliente.objects.all().order_by('nome')
    return render(request, 'crediario/clientes_list.html', {'clientes': clientes})

def cliente_detail(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    notas = cliente.notas.order_by('-data_nota')[:20]
    return render(request, 'crediario/cliente_detail.html', {'cliente': cliente, 'notas': notas})

# --- Notas (create with items) ---
def nota_list(request):
    notas = Nota.objects.select_related('cliente').order_by('-data_nota')[:100]
    return render(request, 'crediario/nota_list.html', {'notas': notas})

def nota_detail(request, pk):
    nota = get_object_or_404(Nota, pk=pk)
    itens = nota.itens.all()
    anexos = nota.anexos.all()
    pagamentos = nota.pagamentos.all()
    return render(request, 'crediario/nota_detail.html', {
        'nota': nota, 'itens': itens, 'anexos': anexos, 'pagamentos': pagamentos
    })

def nota_create(request):
    if request.method == 'POST':
        form = NotaForm(request.POST)
        formset = ItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                nota = form.save(commit=False)
                # Temporarily set total 0; will compute after items saved
                nota.total = Decimal('0.00')
                nota.save()
                total = Decimal('0.00')
                for item_form in formset:
                    if not item_form.cleaned_data:
                        continue
                    descricao = item_form.cleaned_data.get('descricao')
                    quantidade = item_form.cleaned_data.get('quantidade') or Decimal('0')
                    preco = item_form.cleaned_data.get('preco_unitario') or Decimal('0')
                    if descricao is None:
                        continue
                    item = ItemNota(
                        nota=nota,
                        descricao=descricao,
                        quantidade=quantidade,
                        preco_unitario=preco,
                        subtotal=(quantidade * preco).quantize(Decimal('0.01'))
                    )
                    item.save()
                    total += item.subtotal
                # valida limite de crediario do cliente
                cliente = nota.cliente
                novo_saldo = (cliente.saldo_devedor or Decimal('0.00')) + total
                if cliente.limite_crediario is not None and novo_saldo > cliente.limite_crediario:
                    # rollback atomic
                    transaction.set_rollback(True)
                    messages.error(request, f'Limite de crediário excedido: limite {cliente.limite_crediario} / novo saldo {novo_saldo}')
                else:
                    # atualiza total da nota e saldo do cliente
                    nota.total = total
                    nota.save(update_fields=['total'])
                    cliente.saldo_devedor = novo_saldo
                    cliente.save(update_fields=['saldo_devedor'])
                    messages.success(request, 'Nota criada com sucesso.')
                    return redirect('crediario:nota_detail', pk=nota.pk)
    else:
        form = NotaForm()
        formset = ItemFormSet()
    return render(request, 'crediario/nota_form.html', {'form': form, 'formset': formset})

# --- Pagamentos simples ---
def pagamento_create(request):
    if request.method == 'POST':
        form = PagamentoForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                pagamento = form.save()   # model.Pagamento.save() faz a atualização do saldo
                # NÃO atualize o cliente aqui — o model já faz isso.
                # Também o model chama nota.update_status_after_pagamentos() se a implementação existir.
                messages.success(request, 'Pagamento registrado.')
                if pagamento.nota:
                    return redirect('crediario:nota_detail', pk=pagamento.nota.pk)
                else:
                    return redirect('crediario:nota_list')
    else:
        form = PagamentoForm()
    return render(request, 'crediario/pagamento_form.html', {'form': form})