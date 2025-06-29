# apps/badgrsocialauth/management/commands/teste_oauth_ufsc.py

import requests
import urllib.parse
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Testa o fluxo OAuth UFSC interativamente'

    def add_arguments(self, parser):
        parser.add_argument(
            '--client-id',
            type=str,
            default='edx-badges',
            help='Client ID do OAuth UFSC (padrão: edx-badges)'
        )
        parser.add_argument(
            '--client-secret',
            type=str,
            default='sdf46sdfgsddfg',
            help='Client Secret do OAuth UFSC'
        )
        parser.add_argument(
            '--base-url',
            type=str,
            default='https://api-badges.setic.ufsc.br',
            help='URL base do Django (padrão: https://api-badges.setic.ufsc.br)'
        )
        parser.add_argument(
            '--auth-url',
            type=str,
            default='https://sistemas.ufsc.br/oauth2.0/authorize',
            help='URL de autorização da UFSC'
        )
        parser.add_argument(
            '--token-url',
            type=str,
            default='https://sistemas.ufsc.br/oauth2.0/accessToken',
            help='URL de token da UFSC'
        )
        parser.add_argument(
            '--profile-url',
            type=str,
            default='https://sistemas.ufsc.br/oauth2.0/profile',
            help='URL de perfil da UFSC'
        )
        parser.add_argument(
            '--auto-code',
            type=str,
            help='Código de autorização (pula a interação manual)'
        )

    def handle(self, *args, **options):
        # Configurações
        client_id = options['client_id']
        client_secret = options['client_secret']
        base_url = options['base_url']
        auth_url = options['auth_url']
        token_url = options['token_url']
        profile_url = options['profile_url']
        
        # O REDIRECT_URI deve corresponder exatamente ao registrado na UFSC
        redirect_uri = f"{base_url}/accounts/ufsc/login/callback/"
        
        # Escopos padrão
        scopes = ['openid', 'profile', 'email']

        self.stdout.write(self.style.SUCCESS("\n=== TESTE DE FLUXO OAUTH UFSC ==="))
        self.stdout.write(f"CLIENT_ID: {client_id}")
        self.stdout.write(f"CLIENT_SECRET: {client_secret}")
        self.stdout.write(f"REDIRECT_URI: {redirect_uri}")
        self.stdout.write(self.style.WARNING("⚠️  VERIFIQUE SE O REDIRECT_URI ESTÁ EXATAMENTE IGUAL AO REGISTRADO NA UFSC"))
        self.stdout.write(f"AUTH_URL: {auth_url}")
        self.stdout.write(f"TOKEN_URL: {token_url}")
        self.stdout.write(f"PROFILE_URL: {profile_url}")

        # Passo 1: Gerar URL de autorização
        self.stdout.write(self.style.SUCCESS("\n--- Passo 1: Gerando URL de Autorização ---"))
        auth_params = {
            'response_type': 'code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'scope': ' '.join(scopes),
            'state': 'badgr_oauth_test_state'  # Estado para prevenir CSRF
        }
        authorization_url = f"{auth_url}?{urllib.parse.urlencode(auth_params)}"
        
        self.stdout.write("URL de autorização gerada:")
        self.stdout.write(self.style.HTTP_INFO(authorization_url))
        self.stdout.write("\n📋 Copie e abra esta URL no navegador")
        self.stdout.write("🔑 Complete o login na UFSC")
        self.stdout.write("📋 Copie o 'code' da URL de redirecionamento")

        # Passo 2: Obter código de autorização
        if options['auto_code']:
            auth_code = options['auto_code']
            self.stdout.write(f"\n--- Usando código fornecido: {auth_code} ---")
        else:
            auth_code = input("\n--- Digite o código de autorização da URL de callback: ")

        if not auth_code:
            self.stdout.write(self.style.ERROR("❌ Código de autorização não fornecido. Encerrando teste."))
            return

        # Passo 3: Trocar código por token
        self.stdout.write(self.style.SUCCESS("\n--- Passo 3: Trocando código por token de acesso ---"))
        token_params = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret,
        }

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        try:
            self.stdout.write("📡 Fazendo requisição para obter token...")
            token_response = requests.post(token_url, data=token_params, headers=headers, timeout=30)
            
            self.stdout.write(f"📊 Status da resposta: {token_response.status_code}")
            self.stdout.write(f"📊 Headers da resposta: {dict(token_response.headers)}")
            
            # Tentar decodificar JSON, mas mostrar texto bruto se falhar
            try:
                token_data = token_response.json()
                self.stdout.write("📋 Resposta do token (JSON):")
                self.stdout.write(self.style.HTTP_INFO(str(token_data)))
            except ValueError:
                self.stdout.write("⚠️  Resposta não é JSON válido. Conteúdo bruto:")
                self.stdout.write(self.style.HTTP_INFO(token_response.text))
                return

            token_response.raise_for_status()  # Levanta erro para status HTTP ruins

            access_token = token_data.get('access_token')
            if access_token:
                self.stdout.write(self.style.SUCCESS(f"✅ Token de Acesso Obtido: {access_token}"))

                # Passo 4: Obter informações do usuário
                self.stdout.write(self.style.SUCCESS("\n--- Passo 4: Obtendo informações do usuário ---"))
                user_headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Accept': 'application/json'
                }
                
                self.stdout.write("📡 Fazendo requisição para obter dados do usuário...")
                userinfo_response = requests.get(profile_url, headers=user_headers, timeout=30)
                
                self.stdout.write(f"📊 Status da resposta: {userinfo_response.status_code}")
                
                try:
                    userinfo_data = userinfo_response.json()
                    self.stdout.write("📋 Informações do Usuário (JSON):")
                    self.stdout.write(self.style.HTTP_INFO(str(userinfo_data)))
                    
                    # Análise dos campos disponíveis
                    self.stdout.write(self.style.SUCCESS("\n--- Análise dos Campos Disponíveis ---"))
                    if 'attributes' in userinfo_data:
                        attributes = userinfo_data['attributes']
                        self.stdout.write("📋 Campos em 'attributes':")
                        for key, value in attributes.items():
                            self.stdout.write(f"  - {key}: {value}")
                    
                    # Mapeamento sugerido para Badgr
                    self.stdout.write(self.style.SUCCESS("\n--- Mapeamento Sugerido para Badgr ---"))
                    attributes = userinfo_data.get('attributes', {})
                    
                    username = attributes.get('login', 'usuario_ufsc')
                    email = attributes.get('email', 'usuario@ufsc.br')
                    nome_completo = (attributes.get('nomeSocial') or 
                                   attributes.get('nome') or 
                                   attributes.get('personName') or '')
                    
                    nome_parts = nome_completo.split(' ') if nome_completo else []
                    first_name = nome_parts[0] if nome_parts else username
                    last_name = ' '.join(nome_parts[1:]) if len(nome_parts) > 1 else ''
                    
                    self.stdout.write(f"  - username: {username}")
                    self.stdout.write(f"  - email: {email}")
                    self.stdout.write(f"  - first_name: {first_name}")
                    self.stdout.write(f"  - last_name: {last_name}")
                    
                except ValueError:
                    self.stdout.write("⚠️  Resposta de userinfo não é JSON válido:")
                    self.stdout.write(self.style.HTTP_INFO(userinfo_response.text))
                    
                userinfo_response.raise_for_status()
                
            else:
                self.stdout.write(self.style.ERROR("❌ Token de acesso não encontrado na resposta"))

        except requests.exceptions.HTTPError as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro HTTP: {e.response.status_code}"))
            self.stdout.write(self.style.ERROR(f"Resposta: {e.response.text}"))
            
        except requests.exceptions.ConnectionError as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro de Conexão: {e}"))
            self.stdout.write("🔍 Verifique se as URLs estão corretas e se há conectividade")
            
        except requests.exceptions.Timeout as e:
            self.stdout.write(self.style.ERROR(f"❌ Timeout: {e}"))
            
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro na requisição: {e}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro inesperado: {e}"))

        self.stdout.write(self.style.SUCCESS("\n=== TESTE CONCLUÍDO ==="))
        
        # Dicas para debugging
        self.stdout.write(self.style.WARNING("\n💡 DICAS PARA DEBUGGING:"))
        self.stdout.write("1. Verifique se o REDIRECT_URI está exatamente igual ao registrado na UFSC")
        self.stdout.write("2. Confirme se o CLIENT_ID e CLIENT_SECRET estão corretos")
        self.stdout.write("3. Teste primeiro em ambiente de homologação da UFSC")
        self.stdout.write("4. Verifique se não há firewall bloqueando as requisições")
        self.stdout.write("5. Confirme se as URLs dos endpoints da UFSC estão corretas")
