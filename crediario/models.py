from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

class Cliente(models.Model):
    nome = models.CharField(max_length=200)
    telefone = models.CharField(max_length=30, blank=True, null=True, db_index=True)
    endereco = models.TextField(blank=True, null=True)
    limite_crediario = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    saldo_devedor = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clientes'
        indexes = [
            models.Index(fields=['telefone'], name='idx_clientes_telefone'),
            models.Index(fields=['saldo_devedor'], name='idx_clientes_saldo'),
        ]
        ordering = ['nome']

    def __str__(self):
        return self.nome

class Nota(models.Model):
    STATUS_ABERTA = 'aberta'
    STATUS_PARCIAL = 'parcial'
    STATUS_PAGA = 'paga'
    STATUS_CANCELADA = 'cancelada'
    STATUS_CHOICES = [
        (STATUS_ABERTA, 'Aberta'),
        (STATUS_PARCIAL, 'Parcial'),
        (STATUS_PAGA, 'Paga'),
        (STATUS_CANCELADA, 'Cancelada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='notas')
    numero_nota = models.CharField(max_length=50, null=True, blank=True)
    data_nota = models.DateField(default=timezone.localdate)
    vencimento = models.DateField(blank=True, null=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ABERTA)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notas'
        indexes = [
            models.Index(fields=['vencimento'], name='idx_notas_vencimento'),
            models.Index(fields=['status', 'data_nota'], name='idx_notas_status_data'),
        ]
        ordering = ['-data_nota']

    def __str__(self):
        return f'Nota {self.pk} — {self.cliente.nome} — R$ {self.total}'

    def recompute_total(self):
        soma = self.itens.aggregate(total=models.Sum('subtotal'))['total'] or Decimal('0.00')
        if soma != self.total:
            self.total = soma
            self.save(update_fields=['total', 'atualizado_em'])

    def update_status_after_pagamentos(self):
        total_pago = self.pagamentos.aggregate(total=models.Sum('valor_pagamento'))['total'] or Decimal('0.00')
        if total_pago >= self.total:
            novo = self.STATUS_PAGA
        elif total_pago > 0:
            novo = self.STATUS_PARCIAL
        else:
            novo = self.STATUS_ABERTA
        if novo != self.status:
            self.status = novo
            self.save(update_fields=['status', 'atualizado_em'])

    def save(self, *args, **kwargs):
        """
        Ao salvar a nota, garantimos que o cliente.saldo_devedor seja ajustado
        apenas pela diferença entre o novo total e o antigo (delta).
        """
        # obter valor anterior (antes de salvar) — 0 se nova
        old_total = Decimal('0.00')
        if self.pk:
            try:
                old_total = Nota.objects.values_list('total', flat=True).get(pk=self.pk) or Decimal('0.00')
            except Nota.DoesNotExist:
                old_total = Decimal('0.00')

        # chama super para persistir mudança do total caso já tenha sido setado
        super().save(*args, **kwargs)

        # depois de salvo, read total atual (em caso de quantization)
        new_total = self.total or Decimal('0.00')
        delta = new_total - (old_total or Decimal('0.00'))

        if delta != Decimal('0.00'):
            # atualiza cliente com lock para evitar race conditions
            with transaction.atomic():
                cliente = Cliente.objects.select_for_update().get(pk=self.cliente_id)
                cliente.saldo_devedor = (cliente.saldo_devedor or Decimal('0.00')) + delta
                cliente.save(update_fields=['saldo_devedor', 'atualizado_em'])

    def recompute_total(self):
        soma = self.itens.aggregate(total=models.Sum('subtotal'))['total'] or Decimal('0.00')
        if soma != self.total:
            # atualiza total e aciona save para aplicar delta corretamente
            self.total = soma
            # salva usando o método save acima que aplica delta ao cliente
            self.save(update_fields=['total', 'atualizado_em'])        

class ItemNota(models.Model):
    nota = models.ForeignKey(Nota, on_delete=models.CASCADE, related_name='itens')
    descricao = models.TextField()
    quantidade = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal('1.0000'))
    preco_unitario = models.DecimalField(max_digits=18, decimal_places=4)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'itens_nota'
        ordering = ['criado_em']

    def __str__(self):
        return f'{self.descricao} ({self.quantidade} x {self.preco_unitario})'

    def save(self, *args, **kwargs):
        """
        Calculate subtotal and update the parent Nota total in a transaction-safe way.
        This avoids partial updates and ensures the Nota.recompute_total() runs after
        the item is saved. We refresh the nota from DB before recomputing to
        reduce the chance of stale reads.
        """
        # calculate subtotal before saving
        if self.quantidade is not None and self.preco_unitario is not None:
            self.subtotal = (self.quantidade * self.preco_unitario).quantize(Decimal('0.01'))

        # Save item and then recompute note total inside a transaction
        with transaction.atomic():
            super().save(*args, **kwargs)
            # make sure we have the latest nota instance before recomputing
            # (nota is required by model, so it should exist)
            self.nota.refresh_from_db()
            self.nota.recompute_total()

class Pagamento(models.Model):
    nota = models.ForeignKey(Nota, on_delete=models.SET_NULL, related_name='pagamentos', null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pagamentos')
    valor_pagamento = models.DecimalField(max_digits=12, decimal_places=2)
    data_pagamento = models.DateField(default=timezone.localdate)
    metodo = models.CharField(max_length=50, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pagamentos'
        indexes = [
            models.Index(fields=['nota'], name='idx_pagamentos_nota'),
            models.Index(fields=['cliente'], name='idx_pagamentos_cliente'),
        ]
        ordering = ['-data_pagamento']

    def __str__(self):
        return f'Pagamento {self.pk} — R$ {self.valor_pagamento}'

    def save(self, *args, **kwargs):
        """
        Atualiza o saldo do cliente de forma idempotente e previne pagamentos que
        excedam o valor devido na nota. Usa transaction + select_for_update para
        evitar condições de corrida.
        """
        is_create = self.pk is None

        # lê valor anterior se existe (antes de salvar)
        old_val = None
        if not is_create:
            try:
                old_val = Pagamento.objects.get(pk=self.pk).valor_pagamento
            except Pagamento.DoesNotExist:
                old_val = None

        new_val = self.valor_pagamento or Decimal('0.00')
        old_val = old_val or Decimal('0.00')
        delta = new_val - old_val  # se positivo, reduz saldo (cliente deve menos)

        # salve o pagamento dentro de uma transação com lock no cliente
        with transaction.atomic():
            # lock cliente row to avoid concurrent updates
            cliente = Cliente.objects.select_for_update().get(pk=self.cliente_id)

            # --- REGRA: impedir pagamento maior que o valor devido ---
            if self.nota_id:
                total_pago = self.nota.pagamentos.aggregate(
                    total=models.Sum('valor_pagamento')
                )['total'] or Decimal('0.00')

                falta = (self.nota.total or Decimal('0.00')) - total_pago
                excesso = delta if self.pk else new_val

                if excesso > falta:
                    from django.core.exceptions import ValidationError
                    valor_formatado = f"{falta:.2f}".replace('.', ',')
                    raise ValidationError(
                        f"Pagamento excede o valor devido. Falta pagar apenas R$ {valor_formatado}."
                    )
            # ---------------------------------------------------------

            # salva/atualiza pagamento
            super().save(*args, **kwargs)

            # atualizar saldo com base no delta
            cliente.saldo_devedor = (cliente.saldo_devedor or Decimal('0.00')) - delta
            cliente.save(update_fields=['saldo_devedor', 'atualizado_em'])

            # atualizar status da nota (se aplicável)
            if self.nota_id:
                # refresh nota from db in case it changed
                self.nota.refresh_from_db()
                self.nota.update_status_after_pagamentos()

class Anexo(models.Model):
    nota = models.ForeignKey(Nota, on_delete=models.CASCADE, related_name='anexos')
    arquivo = models.FileField(upload_to='notas/')
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    tamanho_bytes = models.BigIntegerField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'anexos'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.arquivo.name}'

class Notificacao(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, related_name='notificacoes', null=True, blank=True)
    nota = models.ForeignKey(Nota, on_delete=models.SET_NULL, related_name='notificacoes', null=True, blank=True)
    tipo = models.CharField(max_length=50)
    canal = models.CharField(max_length=20, default='log')
    destinatario = models.CharField(max_length=200, blank=True, null=True)
    conteudo = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='pendente')
    tentativa = models.IntegerField(default=0)
    data_agendada = models.DateTimeField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    enviado_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'notificacoes'
        indexes = [
            models.Index(fields=['nota', 'tipo', 'data_agendada'], name='idx_notif_nota_tipo_data'),
        ]
        ordering = ['-data_agendada', '-criado_em']

    def __str__(self):
        return f'Notificação {self.pk} — {self.tipo} — {self.status}'