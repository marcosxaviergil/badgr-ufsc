import os
import pkg_resources
import sys

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from subprocess import call

import mainsite
from mainsite import TOP_DIR


class Command(BaseCommand):
    args = ''
    help = 'Runs build tasks to compile javascript and css'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Force regeneration of swagger files even if they exist',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Iniciando geração dos arquivos Swagger...'))
        
        dirname = os.path.join(TOP_DIR, 'apps', 'mainsite', 'static', 'swagger-ui')
        
        # Criar diretório se não existir
        if not os.path.exists(dirname):
            os.makedirs(dirname)
            self.stdout.write(f'📁 Diretório criado: {dirname}')
        
        # Verificar se já existem arquivos (para evitar regeneração desnecessária)
        force = options.get('force', False)
        if not force:
            existing_files = [
                os.path.join(dirname, 'badgr_spec_v1.json'),
                os.path.join(dirname, 'badgr_spec_v2.json')
            ]
            all_exist = all(os.path.exists(f) for f in existing_files)
            if all_exist:
                self.stdout.write(self.style.WARNING('⚠️  Arquivos Swagger já existem. Use --force para regenerar.'))
                return

        try:
            # Gerar especificações Swagger
            self.stdout.write('📝 Gerando especificações da API...')
            call_command('generate_swagger_spec',
                output=os.path.join(dirname, 'badgr_spec_{version}.json'),
                preamble=os.path.join(dirname, "API_DESCRIPTION_{version}.md"),
                versions=['v1', 'v2'],
                include_oauth2_security=True
            )
            
            # Verificar arquivos gerados
            generated_files = []
            for version in ['v1', 'v2']:
                spec_file = os.path.join(dirname, f'badgr_spec_{version}.json')
                if os.path.exists(spec_file):
                    size = os.path.getsize(spec_file)
                    generated_files.append(f'badgr_spec_{version}.json ({size} bytes)')
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Falha ao gerar: badgr_spec_{version}.json'))
            
            if generated_files:
                self.stdout.write(self.style.SUCCESS('✅ Arquivos gerados com sucesso:'))
                for file_info in generated_files:
                    self.stdout.write(f'  - {file_info}')
            
            # Criar arquivos estáticos essenciais se não existirem
            self._ensure_static_files(dirname)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao gerar arquivos: {e}'))
            # Se falhar, criar especificações mínimas
            self._create_minimal_specs(dirname)

    def _ensure_static_files(self, dirname):
        """Garantir que arquivos estáticos essenciais existam"""
        
        # Verificar se swagger-ui.css existe
        css_file = os.path.join(dirname, 'swagger-ui.css')
        if not os.path.exists(css_file):
            self.stdout.write('📄 Criando swagger-ui.css básico...')
            css_content = """
/* Swagger UI Basic Styles */
.swagger-ui { font-family: sans-serif; }
.swagger-ui .topbar { background-color: #1b1b1b; padding: 10px 0; }
.swagger-ui .info { margin: 20px 0; }
.swagger-ui .scheme-container { background: #fff; padding: 30px 0; }
"""
            with open(css_file, 'w') as f:
                f.write(css_content)

    def _create_minimal_specs(self, dirname):
        """Criar especificações mínimas se a geração automática falhar"""
        import json
        
        self.stdout.write('🔧 Criando especificações mínimas...')
        
        for version in ['v1', 'v2']:
            spec_file = os.path.join(dirname, f'badgr_spec_{version}.json')
            
            minimal_spec = {
                "swagger": "2.0",
                "info": {
                    "title": "Badgr API",
                    "version": version,
                    "description": "API para gerenciamento de badges digitais - UFSC"
                },
                "host": "api-badges.setic.ufsc.br",
                "schemes": ["https", "http"],
                "basePath": f"/{version}",
                "produces": ["application/json"],
                "consumes": ["application/json"],
                "securityDefinitions": {
                    "oauth2": {
                        "type": "oauth2",
                        "flow": "implicit",
                        "authorizationUrl": "/o/authorize/",
                        "scopes": {
                            "read": "Read access",
                            "write": "Write access"
                        }
                    }
                },
                "paths": {
                    "/": {
                        "get": {
                            "summary": "API Root",
                            "description": "Endpoint raiz da API Badgr",
                            "tags": ["root"],
                            "responses": {
                                "200": {
                                    "description": "Sucesso",
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {
                                                "type": "string",
                                                "example": "Badgr API funcionando"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/auth/token": {
                        "post": {
                            "summary": "Obter Token de Autenticação",
                            "description": "Endpoint para autenticação e obtenção de token",
                            "tags": ["auth"],
                            "parameters": [
                                {
                                    "name": "credentials",
                                    "in": "body",
                                    "required": True,
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "username": {"type": "string"},
                                            "password": {"type": "string"}
                                        }
                                    }
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "Token gerado com sucesso"
                                },
                                "401": {
                                    "description": "Credenciais inválidas"
                                }
                            }
                        }
                    }
                }
            }
            
            with open(spec_file, 'w') as f:
                json.dump(minimal_spec, f, indent=2)
            
            self.stdout.write(f'✅ Criado: badgr_spec_{version}.json')
