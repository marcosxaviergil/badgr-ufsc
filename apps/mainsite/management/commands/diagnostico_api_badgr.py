# apps/mainsite/management/commands/diagnostico_api_badgr.py

import os
import json
import sys
from django.core.management.base import BaseCommand
from django.core.management import call_command, get_commands
from django.conf import settings
from django.urls import get_resolver
import requests
from subprocess import run, PIPE


class Command(BaseCommand):
    help = 'Diagnóstico completo da API Swagger do Badgr - todos os testes da conversa'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-naming',
            action='store_true',
            help='Corrige automaticamente a nomenclatura dos arquivos (api_spec vs badgr_spec)',
        )
        parser.add_argument(
            '--test-urls',
            action='store_true',
            help='Testa URLs via HTTP (requer servidor rodando)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Output mais detalhado',
        )

    def handle(self, *args, **options):
        self.verbose = options.get('verbose', False)
        self.test_urls = options.get('test_urls', False)
        self.fix_naming = options.get('fix_naming', False)
        
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("🔍 DIAGNÓSTICO COMPLETO - SWAGGER API DOCUMENTATION BADGR"))
        self.stdout.write("=" * 80)
        
        # Executar todos os testes
        self.test_1_environment()
        self.test_2_dependencies()
        self.test_3_file_structure()
        self.test_4_management_commands()
        self.test_5_django_settings()
        self.test_6_urls_configuration()
        self.test_7_dist_command_simulation()
        self.test_8_swagger_template()
        self.test_9_real_command_execution()
        self.test_10_permissions()
        self.test_11_final_diagnosis()
        
        if self.test_urls:
            self.test_12_url_testing()
        
        if self.fix_naming:
            self.test_13_fix_naming_issue()
        
        self.test_14_complete_verification()
        self.test_15_final_recommendations()

    def log_info(self, message):
        self.stdout.write(f"[INFO] {message}")

    def log_success(self, message):
        self.stdout.write(self.style.SUCCESS(f"[OK] {message}"))

    def log_warning(self, message):
        self.stdout.write(self.style.WARNING(f"[WARNING] {message}"))

    def log_error(self, message):
        self.stdout.write(self.style.ERROR(f"[ERROR] {message}"))

    def section_header(self, title):
        self.stdout.write("\n")
        self.stdout.write(f"📋 {title}")
        self.stdout.write("=" * 80)

    def test_1_environment(self):
        """1. VERIFICAÇÃO DO AMBIENTE"""
        self.section_header("1. VERIFICAÇÃO DO AMBIENTE")
        
        self.log_info("Verificando Python e Django...")
        python_version = sys.version
        self.stdout.write(f"Python: {python_version}")
        
        try:
            import django
            self.stdout.write(f"Django: {django.VERSION}")
        except ImportError:
            self.log_error("Django não encontrado")
        
        self.log_info("Verificando diretório atual...")
        current_dir = os.getcwd()
        self.stdout.write(f"Diretório atual: {current_dir}")
        
        if self.verbose:
            self.stdout.write("Conteúdo do diretório atual:")
            for item in os.listdir(current_dir)[:10]:  # Limitar output
                self.stdout.write(f"  {item}")
        
        self.log_info("Verificando DJANGO_SETTINGS_MODULE...")
        settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'Não definido')
        self.stdout.write(f"DJANGO_SETTINGS_MODULE: {settings_module}")
        
        self.log_info("Verificando se consegue importar Django settings...")
        try:
            self.stdout.write(f"DEBUG: {settings.DEBUG}")
            self.stdout.write(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
            self.log_success("Settings carregados com sucesso")
        except Exception as e:
            self.log_error(f"Erro ao carregar settings: {e}")

    def test_2_dependencies(self):
        """2. VERIFICAÇÃO DE DEPENDÊNCIAS"""
        self.section_header("2. VERIFICAÇÃO DE DEPENDÊNCIAS")
        
        dependencies = [
            'apispec_drf',
            'rest_framework', 
            'django',
            'apispec',
            'yaml'
        ]
        
        for dep in dependencies:
            try:
                __import__(dep)
                self.log_success(f"{dep} encontrado")
                if self.verbose:
                    try:
                        module = __import__(dep)
                        version = getattr(module, '__version__', 'sem versão')
                        self.stdout.write(f"  Versão: {version}")
                    except:
                        pass
            except ImportError:
                self.log_error(f"{dep} não encontrado")
        
        self.log_info("Verificando comando generate_swagger_spec...")
        commands = get_commands()
        if 'generate_swagger_spec' in commands:
            self.log_success("Comando generate_swagger_spec encontrado")
        else:
            self.log_error("Comando generate_swagger_spec NÃO encontrado")
        
        self.log_info("Comandos relacionados a swagger/spec/docs:")
        related_commands = [cmd for cmd in commands.keys() 
                          if any(word in cmd.lower() for word in ['generate', 'swagger', 'spec', 'dist', 'doc'])]
        for cmd in related_commands:
            self.stdout.write(f"  - {cmd}")

    def test_3_file_structure(self):
        """3. VERIFICAÇÃO DA ESTRUTURA DE ARQUIVOS"""
        self.section_header("3. VERIFICAÇÃO DA ESTRUTURA DE ARQUIVOS")
        
        # Definir base paths
        if hasattr(settings, 'BASE_DIR'):
            base_dir = settings.BASE_DIR
        else:
            # Fallback para projetos antigos
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        apps_dir = os.path.join(base_dir, 'apps')
        mainsite_dir = os.path.join(apps_dir, 'mainsite')
        static_dir = os.path.join(mainsite_dir, 'static')
        swagger_dir = os.path.join(static_dir, 'swagger-ui')
        templates_dir = os.path.join(mainsite_dir, 'templates')
        
        directories_to_check = [
            ('apps', apps_dir),
            ('apps/mainsite', mainsite_dir),
            ('apps/mainsite/static', static_dir),
            ('apps/mainsite/static/swagger-ui', swagger_dir),
            ('apps/mainsite/templates', templates_dir),
        ]
        
        for desc, path in directories_to_check:
            if os.path.exists(path):
                self.log_success(f"Diretório '{desc}' encontrado")
                if self.verbose and desc == 'apps/mainsite/static/swagger-ui':
                    self.stdout.write("Conteúdo do swagger-ui:")
                    for item in os.listdir(path):
                        self.stdout.write(f"  {item}")
            else:
                self.log_error(f"Diretório '{desc}' NÃO encontrado")
        
        # Verificar arquivos específicos
        files_to_check = [
            f'{mainsite_dir}/management/commands/dist.py',
            f'{swagger_dir}/api_spec_v1.json',
            f'{swagger_dir}/api_spec_v2.json', 
            f'{swagger_dir}/badgr_spec_v1.json',
            f'{swagger_dir}/badgr_spec_v2.json',
            f'{swagger_dir}/swagger-ui.css',
            f'{swagger_dir}/swagger-ui-bundle.js',
            f'{swagger_dir}/swagger-ui-standalone-preset.js',
            f'{templates_dir}/entity/swagger-docs.html',
            f'{templates_dir}/swagger-docs.html',
        ]
        
        self.log_info("Verificando arquivos específicos...")
        for file_path in files_to_check:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                self.log_success(f"Arquivo encontrado: {os.path.basename(file_path)} ({size} bytes)")
            else:
                self.log_warning(f"Arquivo NÃO encontrado: {os.path.basename(file_path)}")

    def test_4_management_commands(self):
        """4. VERIFICAÇÃO DOS COMANDOS DE MANAGEMENT"""
        self.section_header("4. VERIFICAÇÃO DOS COMANDOS DE MANAGEMENT")
        
        # Verificar comando dist
        dist_path = None
        possible_paths = [
            'apps/mainsite/management/commands/dist.py',
            os.path.join(settings.BASE_DIR if hasattr(settings, 'BASE_DIR') else '.', 
                        'apps/mainsite/management/commands/dist.py')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                dist_path = path
                break
        
        if dist_path:
            self.log_success("Arquivo dist.py encontrado")
            if self.verbose:
                self.stdout.write("Conteúdo do comando dist.py:")
                self.stdout.write("-" * 40)
                try:
                    with open(dist_path, 'r') as f:
                        content = f.read()
                        self.stdout.write(content)
                except Exception as e:
                    self.log_error(f"Erro ao ler dist.py: {e}")
                self.stdout.write("-" * 40)
        else:
            self.log_error("Arquivo dist.py NÃO encontrado")
        
        # Verificar se comandos estão registrados
        commands = get_commands()
        for cmd in ['dist', 'generate_swagger_spec']:
            if cmd in commands:
                self.log_success(f"Comando '{cmd}' está registrado")
            else:
                self.log_error(f"Comando '{cmd}' NÃO está registrado")

    def test_5_django_settings(self):
        """5. VERIFICAÇÃO DAS CONFIGURAÇÕES DO DJANGO"""
        self.section_header("5. VERIFICAÇÃO DAS CONFIGURAÇÕES DO DJANGO")
        
        self.log_info("Verificando INSTALLED_APPS...")
        required_apps = ['rest_framework', 'apispec_drf', 'mainsite']
        
        for app in required_apps:
            if app in settings.INSTALLED_APPS:
                self.log_success(f"{app} está em INSTALLED_APPS")
            else:
                self.log_error(f"{app} NÃO está em INSTALLED_APPS")
        
        if self.verbose:
            self.stdout.write("INSTALLED_APPS completo:")
            for app in settings.INSTALLED_APPS:
                self.stdout.write(f"  - {app}")
        
        self.log_info("Verificando configurações de arquivos estáticos...")
        static_settings = [
            ('STATIC_URL', getattr(settings, 'STATIC_URL', 'Não definido')),
            ('STATIC_ROOT', getattr(settings, 'STATIC_ROOT', 'Não definido')),
            ('STATICFILES_DIRS', getattr(settings, 'STATICFILES_DIRS', 'Não definido')),
            ('MEDIA_URL', getattr(settings, 'MEDIA_URL', 'Não definido')),
            ('MEDIA_ROOT', getattr(settings, 'MEDIA_ROOT', 'Não definido')),
        ]
        
        for setting_name, setting_value in static_settings:
            self.stdout.write(f"{setting_name}: {setting_value}")

    def test_6_urls_configuration(self):
        """6. VERIFICAÇÃO DAS URLs"""
        self.section_header("6. VERIFICAÇÃO DAS URLs")
        
        self.log_info("Verificando configuração de URLs...")
        try:
            # Tentar encontrar urls.py
            urls_paths = [
                'apps/mainsite/urls.py',
                os.path.join(settings.BASE_DIR if hasattr(settings, 'BASE_DIR') else '.', 
                           'apps/mainsite/urls.py')
            ]
            
            urls_content = None
            for path in urls_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        urls_content = f.read()
                    break
            
            if urls_content:
                # Procurar por padrões relacionados a docs
                if 'docs' in urls_content.lower():
                    self.log_success("Configurações de docs encontradas em urls.py")
                    if self.verbose:
                        lines = urls_content.split('\n')
                        for i, line in enumerate(lines):
                            if 'docs' in line.lower() or 'swagger' in line.lower() or 'apispec' in line.lower():
                                self.stdout.write(f"  Linha {i+1}: {line.strip()}")
                else:
                    self.log_warning("Nenhuma configuração de docs encontrada em urls.py")
                
                if 'apispec_drf' in urls_content:
                    self.log_success("apispec_drf.urls encontrado em urls.py")
                else:
                    self.log_warning("apispec_drf.urls NÃO encontrado em urls.py")
            else:
                self.log_error("Arquivo urls.py não encontrado")
        
        except Exception as e:
            self.log_error(f"Erro ao verificar URLs: {e}")

    def test_7_dist_command_simulation(self):
        """7. TESTE DO COMANDO DIST (SIMULAÇÃO)"""
        self.section_header("7. TESTE DO COMANDO DIST (SIMULAÇÃO)")
        
        try:
            from mainsite import TOP_DIR
            dirname = os.path.join(TOP_DIR, 'apps', 'mainsite', 'static', 'swagger-ui')
            
            self.stdout.write(f"TOP_DIR: {TOP_DIR}")
            self.stdout.write(f"Diretório alvo: {dirname}")
            self.stdout.write(f"Existe: {os.path.exists(dirname)}")
            
            if not os.path.exists(dirname):
                self.log_warning("Diretório seria criado pelo comando dist")
            
            output_pattern = os.path.join(dirname, 'api_spec_{version}.json')
            preamble_pattern = os.path.join(dirname, 'API_DESCRIPTION_{version}.md')
            
            self.stdout.write(f"Padrão de output: {output_pattern}")
            self.stdout.write(f"Padrão de preamble: {preamble_pattern}")
            
            # Verificar se o comando generate_swagger_spec existe
            commands = get_commands()
            if 'generate_swagger_spec' in commands:
                self.log_success("Comando generate_swagger_spec disponível")
            else:
                self.log_error("Comando generate_swagger_spec NÃO disponível")
        
        except Exception as e:
            self.log_error(f"Erro ao testar comando dist: {e}")

    def test_8_swagger_template(self):
        """8. VERIFICAÇÃO DO TEMPLATE SWAGGER"""
        self.section_header("8. VERIFICAÇÃO DO TEMPLATE SWAGGER")
        
        template_paths = [
            'apps/mainsite/templates/swagger-docs.html',
            'apps/mainsite/templates/entity/swagger-docs.html',
        ]
        
        if hasattr(settings, 'BASE_DIR'):
            base_dir = settings.BASE_DIR
            template_paths.extend([
                os.path.join(base_dir, 'apps/mainsite/templates/swagger-docs.html'),
                os.path.join(base_dir, 'apps/mainsite/templates/entity/swagger-docs.html'),
            ])
        
        template_found = False
        for template_path in template_paths:
            if os.path.exists(template_path):
                template_found = True
                self.log_success(f"Template encontrado: {template_path}")
                
                if self.verbose:
                    self.stdout.write("Conteúdo do template:")
                    self.stdout.write("-" * 40)
                    try:
                        with open(template_path, 'r') as f:
                            content = f.read()
                            # Mostrar apenas linhas relevantes
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                if 'api_spec' in line or 'badgr_spec' in line:
                                    self.stdout.write(f"  Linha {i+1}: {line.strip()}")
                    except Exception as e:
                        self.log_error(f"Erro ao ler template: {e}")
                    self.stdout.write("-" * 40)
                break
        
        if not template_found:
            self.log_error("Template swagger-docs.html NÃO encontrado")
        
        # Procurar templates relacionados
        self.log_info("Procurando todos os templates relacionados...")
        for root, dirs, files in os.walk('.'):
            for file in files:
                if 'swagger' in file.lower() and file.endswith('.html'):
                    self.stdout.write(f"  Encontrado: {os.path.join(root, file)}")

    def test_9_real_command_execution(self):
        """9. TESTE DE EXECUÇÃO REAL DOS COMANDOS"""
        self.section_header("9. TESTE DE EXECUÇÃO REAL DOS COMANDOS")
        
        self.log_info("Testando comando dist...")
        try:
            call_command('dist')
            self.log_success("Comando dist executado com sucesso")
        except Exception as e:
            self.log_error(f"Comando dist falhou: {e}")
        
        self.log_info("Testando comando collectstatic (dry-run)...")
        try:
            call_command('collectstatic', '--dry-run', '--noinput')
            self.log_success("Comando collectstatic (dry-run) executado com sucesso")
        except Exception as e:
            self.log_error(f"Comando collectstatic falhou: {e}")

    def test_10_permissions(self):
        """10. VERIFICAÇÃO DE PERMISSÕES"""
        self.section_header("10. VERIFICAÇÃO DE PERMISSÕES")
        
        paths_to_check = [
            'apps/mainsite/static',
            'apps/mainsite/static/swagger-ui',
        ]
        
        if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
            paths_to_check.append(settings.STATIC_ROOT)
            paths_to_check.append(os.path.join(settings.STATIC_ROOT, 'swagger-ui'))
        
        for path in paths_to_check:
            if os.path.exists(path):
                if os.access(path, os.W_OK):
                    self.log_success(f"Diretório {path} é gravável")
                else:
                    self.log_error(f"Diretório {path} NÃO é gravável")
                
                if self.verbose:
                    try:
                        stat_info = os.stat(path)
                        self.stdout.write(f"  Permissões: {oct(stat_info.st_mode)[-3:]}")
                    except:
                        pass
            else:
                self.log_warning(f"Diretório {path} não existe")

    def test_11_final_diagnosis(self):
        """11. RESUMO DO DIAGNÓSTICO"""
        self.section_header("11. RESUMO DO DIAGNÓSTICO")
        
        issues = []
        recommendations = []
        
        # Verificar Django
        try:
            import django
            self.log_success("Django configurado corretamente")
        except Exception as e:
            issues.append(f"Django não configurado: {e}")
        
        # Verificar apispec_drf
        try:
            import apispec_drf
            self.log_success("apispec_drf disponível")
        except ImportError:
            issues.append("apispec_drf não instalado")
            recommendations.append("Instalar: pip install apispec_drf")
        
        # Verificar comandos
        commands = get_commands()
        if 'generate_swagger_spec' not in commands:
            issues.append("Comando generate_swagger_spec não disponível")
            recommendations.append("Verificar se apispec_drf está em INSTALLED_APPS")
        
        if 'dist' not in commands:
            issues.append("Comando dist não disponível")
            recommendations.append("Verificar apps/mainsite/management/commands/dist.py")
        
        # Verificar diretórios
        swagger_dir = 'apps/mainsite/static/swagger-ui'
        if not os.path.exists(swagger_dir):
            issues.append("Diretório swagger-ui não existe")
            recommendations.append("Executar: python manage.py dist")
        
        # Verificar arquivos Swagger
        swagger_files = [
            'apps/mainsite/static/swagger-ui/api_spec_v1.json',
            'apps/mainsite/static/swagger-ui/api_spec_v2.json',
            'apps/mainsite/static/swagger-ui/badgr_spec_v1.json',
            'apps/mainsite/static/swagger-ui/badgr_spec_v2.json',
        ]
        
        missing_files = []
        for file_path in swagger_files:
            if not os.path.exists(file_path):
                missing_files.append(os.path.basename(file_path))
        
        if missing_files:
            issues.append(f"Arquivos não encontrados: {', '.join(missing_files)}")
            recommendations.append("Executar: python manage.py dist && python manage.py collectstatic")
        
        # Mostrar resultados
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("PROBLEMAS ENCONTRADOS:")
        self.stdout.write("=" * 50)
        if issues:
            for i, issue in enumerate(issues, 1):
                self.stdout.write(f"{i}. {issue}")
        else:
            self.log_success("Nenhum problema crítico encontrado")
        
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("RECOMENDAÇÕES:")
        self.stdout.write("=" * 50)
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                self.stdout.write(f"{i}. {rec}")
        else:
            self.log_success("Nenhuma recomendação necessária")

    def test_12_url_testing(self):
        """12. TESTE DE URLs (OPCIONAL)"""
        self.section_header("12. TESTE DE URLs")
        
        urls_to_test = [
            'http://localhost:8000/docs/v2/',
            'http://localhost:8000/static/swagger-ui/api_spec_v2.json',
            'http://localhost:8000/static/swagger-ui/badgr_spec_v2.json',
            'http://localhost:8000/static/swagger-ui/swagger-ui.css',
        ]
        
        for url in urls_to_test:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.log_success(f"URL acessível: {url}")
                else:
                    self.log_error(f"URL retornou {response.status_code}: {url}")
            except requests.exceptions.RequestException as e:
                self.log_warning(f"Não foi possível testar URL: {url} ({e})")

    def test_13_fix_naming_issue(self):
        """13. CORREÇÃO DO PROBLEMA DE NOMENCLATURA"""
        self.section_header("13. CORREÇÃO DO PROBLEMA DE NOMENCLATURA")
        
        self.log_info("Verificando inconsistência de nomenclatura...")
        
        # Verificar qual padrão está sendo usado
        api_spec_exists = os.path.exists('apps/mainsite/static/swagger-ui/api_spec_v2.json')
        badgr_spec_exists = os.path.exists('apps/mainsite/static/swagger-ui/badgr_spec_v2.json')
        
        # Verificar o que o template espera
        template_paths = [
            'apps/mainsite/templates/swagger-docs.html',
            'apps/mainsite/templates/entity/swagger-docs.html',
        ]
        
        template_expects_badgr = False
        template_expects_api = False
        
        for template_path in template_paths:
            if os.path.exists(template_path):
                with open(template_path, 'r') as f:
                    content = f.read()
                    if 'badgr_spec_' in content:
                        template_expects_badgr = True
                    if 'api_spec_' in content:
                        template_expects_api = True
        
        self.stdout.write(f"Arquivos api_spec existem: {api_spec_exists}")
        self.stdout.write(f"Arquivos badgr_spec existem: {badgr_spec_exists}")
        self.stdout.write(f"Template espera badgr_spec: {template_expects_badgr}")
        self.stdout.write(f"Template espera api_spec: {template_expects_api}")
        
        if template_expects_badgr and api_spec_exists and not badgr_spec_exists:
            self.log_warning("INCONSISTÊNCIA DETECTADA: Template espera badgr_spec mas comando gera api_spec")
            
            # Opção 1: Corrigir o comando dist.py
            dist_path = 'apps/mainsite/management/commands/dist.py'
            if os.path.exists(dist_path):
                self.log_info("CORREÇÃO AUTOMÁTICA: Alterando dist.py para gerar badgr_spec...")
                try:
                    with open(dist_path, 'r') as f:
                        content = f.read()
                    
                    # Fazer backup
                    backup_path = dist_path + '.backup'
                    with open(backup_path, 'w') as f:
                        f.write(content)
                    self.log_info(f"Backup criado: {backup_path}")
                    
                    # Aplicar correção
                    new_content = content.replace("'api_spec_{version}.json'", "'badgr_spec_{version}.json'")
                    
                    with open(dist_path, 'w') as f:
                        f.write(new_content)
                    
                    self.log_success("dist.py corrigido para gerar badgr_spec_{version}.json")
                    
                    # Regenerar arquivos
                    self.log_info("Regenerando arquivos Swagger...")
                    call_command('dist')
                    self.log_success("Arquivos regenerados com nomenclatura correta")
                    
                except Exception as e:
                    self.log_error(f"Erro ao corrigir dist.py: {e}")

    def test_14_complete_verification(self):
        """14. VERIFICAÇÃO COMPLETA PÓS-CORREÇÃO"""
        self.section_header("14. VERIFICAÇÃO COMPLETA PÓS-CORREÇÃO")
        
        # Verificar arquivos JSON
        json_files = [
            'apps/mainsite/static/swagger-ui/api_spec_v1.json',
            'apps/mainsite/static/swagger-ui/api_spec_v2.json',
            'apps/mainsite/static/swagger-ui/badgr_spec_v1.json',
            'apps/mainsite/static/swagger-ui/badgr_spec_v2.json',
        ]
        
        self.log_info("Verificando arquivos JSON...")
        for file_path in json_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        swagger_version = data.get('swagger', 'N/A')
                        title = data.get('info', {}).get('title', 'N/A')
                        paths_count = len(data.get('paths', {}))
                        
                        self.log_success(f"{os.path.basename(file_path)}: {swagger_version}, {title}, {paths_count} endpoints")
                except Exception as e:
                    self.log_error(f"Erro ao verificar {os.path.basename(file_path)}: {e}")
            else:
                self.log_warning(f"Arquivo não encontrado: {os.path.basename(file_path)}")
        
        # Verificar se collectstatic funcionaria
        self.log_info("Verificando collectstatic (dry-run)...")
        try:
            call_command('collectstatic', '--dry-run', '--noinput')
            self.log_success("collectstatic funcionaria corretamente")
        except Exception as e:
            self.log_error(f"collectstatic teria problemas: {e}")
        
        # Verificar staticfiles
        if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
            staticfiles_swagger = os.path.join(settings.STATIC_ROOT, 'swagger-ui')
            if os.path.exists(staticfiles_swagger):
                self.log_success("Diretório swagger-ui existe em STATIC_ROOT")
                if self.verbose:
                    files = os.listdir(staticfiles_swagger)
                    self.stdout.write("Arquivos em staticfiles/swagger-ui:")
                    for file in files:
                        self.stdout.write(f"  {file}")
            else:
                self.log_warning("Diretório swagger-ui não existe em STATIC_ROOT")

    def test_15_final_recommendations(self):
        """15. RECOMENDAÇÕES FINAIS"""
        self.section_header("15. RECOMENDAÇÕES FINAIS E COMANDOS ÚTEIS")
        
        self.stdout.write("PRÓXIMOS PASSOS SUGERIDOS:")
        self.stdout.write("=" * 50)
        self.stdout.write("1. Regenerar arquivos Swagger:")
        self.stdout.write("   python manage.py dist")
        self.stdout.write("")
        self.stdout.write("2. Coletar arquivos estáticos:")
        self.stdout.write("   python manage.py collectstatic --noinput")
        self.stdout.write("")
        self.stdout.write("3. Verificar arquivo JSON diretamente:")
        self.stdout.write("   curl http://localhost:8000/static/swagger-ui/badgr_spec_v2.json")
        self.stdout.write("")
        self.stdout.write("4. Verificar se servidor está servindo estáticos:")
        self.stdout.write("   curl -I http://localhost:8000/static/swagger-ui/swagger-ui.css")
        self.stdout.write("")
        self.stdout.write("5. Testar interface Swagger:")
        self.stdout.write("   curl http://localhost:8000/docs/v2/")
        self.stdout.write("")
        self.stdout.write("6. Limpar cache do navegador:")
        self.stdout.write("   Ctrl+F5 ou Ctrl+Shift+R")
        self.stdout.write("")
        
        # Verificação final de consistência
        self.log_info("Verificação final de consistência...")
        
        # Verificar se arquivos essenciais existem
        essential_files = [
            'apps/mainsite/static/swagger-ui',
            'apps/mainsite/templates/entity/swagger-docs.html',
        ]
        
        all_essential_exist = True
        for file_path in essential_files:
            if not os.path.exists(file_path):
                all_essential_exist = False
                break
        
        # Verificar se pelo menos um conjunto de arquivos JSON existe
        api_spec_v2 = os.path.exists('apps/mainsite/static/swagger-ui/api_spec_v2.json')
        badgr_spec_v2 = os.path.exists('apps/mainsite/static/swagger-ui/badgr_spec_v2.json')
        
        if all_essential_exist and (api_spec_v2 or badgr_spec_v2):
            self.stdout.write("")
            self.stdout.write("🎉 " + "=" * 70)
            self.log_success("DIAGNÓSTICO CONCLUÍDO: Estrutura básica OK")
            self.stdout.write("🎉 " + "=" * 70)
            
            if api_spec_v2 and not badgr_spec_v2:
                self.log_warning("ATENÇÃO: Template pode estar esperando badgr_spec mas encontrou api_spec")
                self.stdout.write("Execute com --fix-naming para corrigir automaticamente")
            elif badgr_spec_v2 and not api_spec_v2:
                self.log_success("Nomenclatura consistente: badgr_spec")
            elif api_spec_v2 and badgr_spec_v2:
                self.log_success("Ambos os formatos de arquivo presentes")
        
        else:
            self.stdout.write("")
            self.stdout.write("❌ " + "=" * 70)
            self.log_error("PROBLEMAS CRÍTICOS DETECTADOS")
            self.stdout.write("❌ " + "=" * 70)
            
            if not all_essential_exist:
                self.log_error("Estrutura de arquivos incompleta")
            
            if not (api_spec_v2 or badgr_spec_v2):
                self.log_error("Nenhum arquivo JSON de especificação encontrado")
                self.stdout.write("Execute: python manage.py dist")
        
        # Informações de debug adicionais
        self.stdout.write("")
        self.stdout.write("INFORMAÇÕES DE DEBUG:")
        self.stdout.write("=" * 50)
        self.stdout.write("Para debug avançado, verifique:")
        self.stdout.write("- Logs do servidor Django")
        self.stdout.write("- Console do navegador (F12)")
        self.stdout.write("- Network tab para requisições falhando")
        self.stdout.write("- Permissões de arquivo no servidor")
        self.stdout.write("")
        
        # Informações sobre este comando
        self.stdout.write("SOBRE ESTE COMANDO:")
        self.stdout.write("=" * 50)
        self.stdout.write("Este comando executa todos os testes de diagnóstico que foram")
        self.stdout.write("desenvolvidos durante a conversa para identificar problemas")
        self.stdout.write("com a documentação Swagger do Badgr.")
        self.stdout.write("")
        self.stdout.write("Opções disponíveis:")
        self.stdout.write("--fix-naming    : Corrige automaticamente nomenclatura")
        self.stdout.write("--test-urls     : Testa URLs via HTTP (servidor deve estar rodando)")
        self.stdout.write("--verbose       : Output mais detalhado")
        self.stdout.write("")
        self.stdout.write("Exemplo de uso completo:")
        self.stdout.write("python manage.py diagnostico_api_badgr --fix-naming --verbose")
        
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write("🏁 DIAGNÓSTICO COMPLETO FINALIZADO")
        self.stdout.write("=" * 80)

    def validate_json_file(self, file_path):
        """Valida se um arquivo JSON está bem formado"""
        try:
            with open(file_path, 'r') as f:
                json.load(f)
            return True, "JSON válido"
        except json.JSONDecodeError as e:
            return False, f"JSON inválido: {e}"
        except Exception as e:
            return False, f"Erro ao ler arquivo: {e}"

    def check_file_permissions(self, file_path):
        """Verifica permissões de um arquivo"""
        if not os.path.exists(file_path):
            return "Arquivo não existe"
        
        permissions = []
        if os.access(file_path, os.R_OK):
            permissions.append("leitura")
        if os.access(file_path, os.W_OK):
            permissions.append("escrita")
        if os.access(file_path, os.X_OK):
            permissions.append("execução")
        
        return f"Permissões: {', '.join(permissions) if permissions else 'nenhuma'}"

    def get_file_info(self, file_path):
        """Obtém informações detalhadas de um arquivo"""
        if not os.path.exists(file_path):
            return None
       
        stat_info = os.stat(file_path)
        return {
            'size': stat_info.st_size,
            'modified': stat_info.st_mtime,
            'permissions': oct(stat_info.st_mode)[-3:],
        }

    def check_template_consistency(self):
        """Verifica consistência entre templates e arquivos gerados"""
        template_paths = [
            'apps/mainsite/templates/swagger-docs.html',
            'apps/mainsite/templates/entity/swagger-docs.html',
        ]
        
        if hasattr(settings, 'BASE_DIR'):
            base_dir = settings.BASE_DIR
            template_paths.extend([
                os.path.join(base_dir, 'apps/mainsite/templates/swagger-docs.html'),
                os.path.join(base_dir, 'apps/mainsite/templates/entity/swagger-docs.html'),
            ])
        
        template_references = {
            'api_spec': False,
            'badgr_spec': False,
        }
        
        for template_path in template_paths:
            if os.path.exists(template_path):
                try:
                    with open(template_path, 'r') as f:
                        content = f.read()
                        if 'api_spec_' in content:
                            template_references['api_spec'] = True
                        if 'badgr_spec_' in content:
                            template_references['badgr_spec'] = True
                except Exception:
                    continue
       
        return template_references

    def check_swagger_files_existence(self):
        """Verifica quais arquivos Swagger existem"""
        base_path = 'apps/mainsite/static/swagger-ui'
        files = {
            'api_spec_v1': os.path.join(base_path, 'api_spec_v1.json'),
            'api_spec_v2': os.path.join(base_path, 'api_spec_v2.json'),
            'badgr_spec_v1': os.path.join(base_path, 'badgr_spec_v1.json'),
            'badgr_spec_v2': os.path.join(base_path, 'badgr_spec_v2.json'),
        }
        
        existence = {}
        for name, path in files.items():
            existence[name] = os.path.exists(path)
        
        return existence

    def analyze_dist_command(self):
        """Analisa o comando dist.py para entender o que ele gera"""
        dist_path = 'apps/mainsite/management/commands/dist.py'
       
        if hasattr(settings, 'BASE_DIR'):
            dist_path = os.path.join(settings.BASE_DIR, dist_path)
        
        if not os.path.exists(dist_path):
            return None
        
        try:
            with open(dist_path, 'r') as f:
                content = f.read()
           
            analysis = {
                'generates_api_spec': 'api_spec_{version}' in content,
                'generates_badgr_spec': 'badgr_spec_{version}' in content,
                'output_pattern': None,
            }
           
            # Extrair padrão de output
            import re
            pattern_match = re.search(r"'([^']*spec_\{version\}\.json)'", content)
            if pattern_match:
                analysis['output_pattern'] = pattern_match.group(1)
            
            return analysis
        except Exception:
            return None

    def comprehensive_health_check(self):
        """Executa uma verificação de saúde abrangente"""
        health = {
            'django_ok': False,
            'apispec_drf_ok': False,
            'commands_ok': False,
            'files_ok': False,
            'templates_ok': False,
            'naming_consistent': False,
        }
       
        # Django
        try:
            import django
            health['django_ok'] = True
        except:
            pass
       
        # apispec_drf
        try:
            import apispec_drf
            health['apispec_drf_ok'] = True
        except:
            pass
        
        # Comandos
        commands = get_commands()
        health['commands_ok'] = all(cmd in commands for cmd in ['dist', 'generate_swagger_spec'])
       
        # Arquivos
        swagger_files = self.check_swagger_files_existence()
        health['files_ok'] = any(swagger_files.values())
       
        # Templates
        template_refs = self.check_template_consistency()
        health['templates_ok'] = any(template_refs.values())
        
        # Consistência de nomenclatura
        dist_analysis = self.analyze_dist_command()
        if dist_analysis and template_refs:
            if dist_analysis['generates_api_spec'] and template_refs['api_spec']:
                health['naming_consistent'] = True
            elif dist_analysis['generates_badgr_spec'] and template_refs['badgr_spec']:
                health['naming_consistent'] = True
       
        return health

    def generate_fix_script(self):
        """Gera um script de correção baseado nos problemas encontrados"""
        health = self.comprehensive_health_check()
        swagger_files = self.check_swagger_files_existence()
        template_refs = self.check_template_consistency()
       
        script_lines = [
            "#!/bin/bash",
            "# Script de correção gerado pelo diagnóstico",
            "echo 'Aplicando correções do Swagger API...'",
            "",
        ]
       
        if not health['files_ok']:
            script_lines.extend([
                "echo 'Gerando arquivos Swagger...'",
                "python manage.py dist",
                "",
            ])
       
        if not health['naming_consistent']:
            if template_refs['badgr_spec'] and swagger_files['api_spec_v2'] and not swagger_files['badgr_spec_v2']:
                script_lines.extend([
                    "echo 'Corrigindo nomenclatura - alterando dist.py...'",
                    "sed -i.backup 's/api_spec_{version}/badgr_spec_{version}/g' apps/mainsite/management/commands/dist.py",
                    "python manage.py dist",
                    "",
                ])
       
        script_lines.extend([
            "echo 'Coletando arquivos estáticos...'",
            "python manage.py collectstatic --noinput",
            "",
            "echo 'Correções aplicadas!'",
            "echo 'Teste: curl http://localhost:8000/docs/v2/'",
        ])
       
        return "\n".join(script_lines)
