from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from crediario.models import Nota, Notificacao

class Command(BaseCommand):
    help = 'Checa notas que vencem em X dias e cria notificações mock'

    def add_arguments(self, parser):
        parser.add_argument('--dias', type=int, default=3, help='Dias até o vencimento')

    def handle(self, *args, **options):
        dias = options['dias']
        target = timezone.localdate() + timedelta(days=dias)
        notas = Nota.objects.filter(vencimento=target, status__in=['aberta','parcial'])
        created = 0
        for n in notas:
            exists = Notificacao.objects.filter(nota=n, tipo='vencimento_aviso', data_agendada__date=target).exists()
            if exists:
                continue
            conteudo = f"Olá {n.cliente.nome}, sua nota #{n.id} de R$ {n.total} vence em {n.vencimento}."
            noti = Notificacao.objects.create(
                cliente=n.cliente,
                nota=n,
                tipo='vencimento_aviso',
                canal='log',
                destinatario=n.cliente.telefone or '',
                conteudo=conteudo,
                status='pendente',
                data_agendada=timezone.now()
            )
            print("MOCK enviar:", noti.destinatario, "|", noti.conteudo)
            noti.status = 'enviada'
            noti.enviado_em = timezone.now()
            noti.save(update_fields=['status', 'enviado_em'])
            created += 1
        self.stdout.write(self.style.SUCCESS(f'Notificações processadas: {created}'))