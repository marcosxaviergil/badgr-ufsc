# apps/badgrsocialauth/management/commands/test_ufsc_oauth.py

from django.core.management.base import BaseCommand
from allauth.socialaccount import providers
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Testa se OAuth UFSC foi configurado manualmente no admin'

    def handle(self, *args, **options):
        self.stdout.write("=== Teste OAuth UFSC - Configuração Manual ===\n")
        
        # 1. Verificar se provider está disponível
        try:
            provider = providers.registry.by_id('ufsc')
            self.stdout.write(self.style.SUCCESS(f"✓ Provider UFSC disponível: {provider.name}"))
        except:
            self.stdout.write(self.style.ERROR("✗ Provider UFSC não encontrado"))
            return
        
        # 2. Verificar se foi configurado no admin
        try:
            app = SocialApp.objects.get(provider='ufsc')
            self.stdout.write(self.style.SUCCESS(f"✓ Configurado no admin: {app.name}"))
            self.stdout.write(f"   Client ID: {app.client_id}")
            self.stdout.write(f"   Sites: {[s.domain for s in app.sites.all()]}")
        except SocialApp.DoesNotExist:
            self.stdout.write(self.style.WARNING("⚠ UFSC não configurado no admin"))
            self.stdout.write("  Configure em: /admin/socialaccount/socialapp/add/")
            self.stdout.write("  Selecione 'UFSC' no dropdown Provider")