# apps/badgeuser/management/commands/simulate_email_confirmation.py

import urllib.parse
from django.core.management.base import BaseCommand
from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from allauth.account.models import EmailConfirmationHMAC
from allauth.account.utils import user_pk_to_url_str
from django.contrib.auth.tokens import default_token_generator
from badgeuser.models import CachedEmailAddress
from mainsite.models import BadgrApp


class Command(BaseCommand):
    help = 'Simula o clique no link de confirmação de email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email do usuário para testar'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        self.stdout.write(self.style.SUCCESS(f'\n=== SIMULANDO CONFIRMAÇÃO DE EMAIL PARA {email} ===\n'))
        
        try:
            # Buscar usuário
            User = get_user_model()
            user = User.objects.get(email=email)
            self.stdout.write(f"✓ Usuário encontrado: {user.email}")
            
            # Buscar email address
            email_address = CachedEmailAddress.objects.get(user=user, email=email)
            self.stdout.write(f"✓ EmailAddress encontrado: {email_address.email}")
            
            if email_address.verified:
                self.stdout.write(self.style.WARNING("⚠ Email já está verificado"))
                return
            
            # Gerar token de confirmação
            confirmation = EmailConfirmationHMAC(email_address)
            key = confirmation.key
            self.stdout.write(f"✓ Token gerado: {key}")
            
            # Gerar token para URL
            temp_key = default_token_generator.make_token(user)
            url_token = f"{user_pk_to_url_str(user)}-{temp_key}"
            self.stdout.write(f"✓ URL token gerado: {url_token}")
            
            # Construir URL completa
            badgr_app = BadgrApp.objects.get_current()
            confirm_url = f"/v1/user/confirmemail/{key}?token={url_token}&a={badgr_app.id}"
            full_url = f"https://api-badges.setic.ufsc.br{confirm_url}"
            
            self.stdout.write(f"✓ URL de confirmação completa:")
            self.stdout.write(f"  {full_url}")
            
            # Simular requisição GET para a URL
            client = Client()
            self.stdout.write(f"\n--- SIMULANDO REQUISIÇÃO GET ---")
            
            response = client.get(confirm_url)
            
            self.stdout.write(f"Status Code: {response.status_code}")
            
            if response.status_code == 302:
                location = response.get('Location', 'Não especificado')
                self.stdout.write(f"Redirecionamento para: {location}")
                
                # Verificar se a URL está correta
                if 'https://https://' in location:
                    self.stdout.write(self.style.ERROR("✗ ERRO: Duplo https:// detectado!"))
                elif location.startswith('https://badges.setic.ufsc.br'):
                    self.stdout.write(self.style.SUCCESS("✓ URL de redirecionamento correta"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠ URL inesperada: {location}"))
            else:
                self.stdout.write(f"Resposta: {response.content.decode()[:200]}...")
            
            # Verificar se email foi verificado
            email_address.refresh_from_db()
            if email_address.verified:
                self.stdout.write(self.style.SUCCESS("✓ Email foi verificado com sucesso!"))
            else:
                self.stdout.write(self.style.ERROR("✗ Email não foi verificado"))
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"✗ Usuário com email {email} não encontrado"))
        except CachedEmailAddress.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"✗ EmailAddress para {email} não encontrado"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Erro: {e}"))
            import traceback
            traceback.print_exc()
