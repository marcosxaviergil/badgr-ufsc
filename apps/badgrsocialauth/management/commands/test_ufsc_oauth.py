# apps/badgrsocialauth/management/commands/test_ufsc_oauth.py

from django.core.management.base import BaseCommand
from django.core.urlresolvers import reverse, NoReverseMatch  # Django 1.11
from allauth.socialaccount import providers
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
import json


class Command(BaseCommand):
    help = 'Testa configuração OAuth UFSC'

    def handle(self, *args, **options):
        self.stdout.write("=== Teste de Configuração OAuth UFSC ===\n")
        
        # 1. Verificar providers registrados
        self.stdout.write("1. Providers registrados:")
        provider_list = providers.registry.get_list()
        for p in provider_list:
            self.stdout.write("   - {}: {}".format(p.id, p.name))
        
        ufsc_provider = providers.registry.by_id('ufsc', None)
        if ufsc_provider:
            self.stdout.write(self.style.SUCCESS("✓ Provider UFSC registrado"))
        else:
            self.stdout.write(self.style.ERROR("✗ Provider UFSC NÃO registrado"))
            return
        
        # 2. Verificar URLs
        self.stdout.write("\n2. URLs do OAuth UFSC:")
        urls_to_test = [
            ('ufsc_login', 'URL de login'),
            ('ufsc_callback', 'URL de callback'),
            ('socialaccount_login', 'URL social login base'),
        ]
        
        for url_name, desc in urls_to_test:
            try:
                url = reverse(url_name)
                self.stdout.write(self.style.SUCCESS("   ✓ {}: {}".format(desc, url)))
            except NoReverseMatch:
                self.stdout.write(self.style.ERROR("   ✗ {}: não encontrada".format(desc)))
        
        # 3. Verificar SocialApp
        self.stdout.write("\n3. SocialApp configurado:")
        try:
            app = SocialApp.objects.get(provider='ufsc')
            self.stdout.write(self.style.SUCCESS("   ✓ Client ID: {}".format(app.client_id)))
            sites = ', '.join([s.domain for s in app.sites.all()])
            self.stdout.write(self.style.SUCCESS("   ✓ Sites: {}".format(sites)))
        except SocialApp.DoesNotExist:
            self.stdout.write(self.style.ERROR("   ✗ SocialApp não configurado no admin"))
            self.stdout.write("   Execute: python manage.py create_ufsc_socialapp")
        
        # 4. URLs de teste
        self.stdout.write("\n4. URLs para testar no navegador:")
        try:
            site = Site.objects.get_current()
            base_url = "https://{}".format(site.domain)
            
            self.stdout.write("   - Login direto: {}/account/ufsc/login/".format(base_url))
            self.stdout.write("   - Via sociallogin: {}/account/sociallogin?provider=ufsc".format(base_url))
        except Exception as e:
            self.stdout.write(self.style.ERROR("   Erro ao gerar URLs: {}".format(str(e))))
