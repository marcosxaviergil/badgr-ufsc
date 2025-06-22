from django.core.management.base import BaseCommand
from externaltools.models import ExternalTool

class Command(BaseCommand):
    help = 'Setup initial external tools for OAuth'

    def handle(self, *args, **options):
        # Criar external tool para OAuth UFSC
        external_tool, created = ExternalTool.objects.get_or_create(
            name="UFSC OAuth Login",
            defaults={
                'label': "Login UFSC",
                'launch_url': "https://badges.setic.ufsc.br/auth/login/ufsc-oauth2/",
                'launch_type': "link",
                'is_enabled': True
            }
        )
        
        if created:
            self.stdout.write(f'External tool criado: {external_tool.name}')
        else:
            self.stdout.write(f'External tool já existe: {external_tool.name}')