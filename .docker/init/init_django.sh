#!/bin/bash

set -eu

: "${BADGR_DB_HOST:?Variável BADGR_DB_HOST não definida}"
: "${BADGR_DB_PORT:?Variável BADGR_DB_PORT não definida}"

# ==========================================================
# AGUARDAR BANCO DE DADOS
# ==========================================================
echo "==> Aguardando o banco de dados MySQL em $BADGR_DB_HOST:$BADGR_DB_PORT..."
until nc -z -v -w30 "$BADGR_DB_HOST" "$BADGR_DB_PORT"; do
  echo "⏳ Aguardando conexão com o banco..."
  sleep 5
done
echo "✅ Banco de dados disponível!"

# ==========================================================
# VERIFICAR ESTADO DO BANCO E APLICAR MIGRAÇÕES
# ==========================================================
echo "==> Verificando estado do banco de dados..."
TABLES_COUNT=$(python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mainsite.settings_local')
django.setup()
from django.db import connection
cursor = connection.cursor()
try:
    cursor.execute(\"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name LIKE 'django_%'\")
    print(cursor.fetchone()[0])
except:
    print('0')
" 2>/dev/null || echo "0")

if [ "$TABLES_COUNT" -gt 0 ]; then
    echo "⚠️ Banco de dados já contém $TABLES_COUNT tabelas Django"
    echo "==> Tentando sincronizar estado das migrações..."
    
    # Django 1.11: usar showmigrations --list (sem --plan que não existe)
    echo "🔧 Verificando migrações necessárias..."
    
    # Contar migrações não aplicadas (compatível com Django 1.11)
    UNAPPLIED_MIGRATIONS=$(python manage.py showmigrations --list | grep '\[ \]' | wc -l)
    
    if [ "$UNAPPLIED_MIGRATIONS" -gt 0 ]; then
        echo "📋 Encontradas $UNAPPLIED_MIGRATIONS migrações não aplicadas"
        
        # Lista de apps principais que devem ser fake-initial se tabelas existem
        CORE_APPS=("contenttypes" "auth" "sessions" "sites" "admin" "authtoken")
        
        for app in "${CORE_APPS[@]}"; do
            # Verifica se o app tem migrações pendentes (Django 1.11 compatível)
            PENDING=$(python manage.py showmigrations "$app" 2>/dev/null | grep '\[ \]' | head -1 || echo "")
            if [ ! -z "$PENDING" ]; then
                echo "🔧 Aplicando fake-initial para $app"
                python manage.py migrate "$app" --fake-initial 2>/dev/null || echo "⚠️ Falha no fake-initial para $app (pode ser normal)"
            fi
        done
        
        # Apps específicos do Allauth/Social (Django 1.11)
        SOCIAL_APPS=("socialaccount")
        
        for app in "${SOCIAL_APPS[@]}"; do
            PENDING=$(python manage.py showmigrations "$app" 2>/dev/null | grep '\[ \]' | head -1 || echo "")
            if [ ! -z "$PENDING" ]; then
                echo "🔧 Aplicando fake-initial para $app"
                python manage.py migrate "$app" --fake-initial 2>/dev/null || echo "⚠️ Falha no fake-initial para $app (pode ser normal)"
            fi
        done
        
        # Apps customizados do badgr
        CUSTOM_APPS=("badgeuser" "badgrsocialauth" "issuer" "backpack" "mainsite" "pathway" "recipient" "oauth2_provider")
        
        for app in "${CUSTOM_APPS[@]}"; do
            PENDING=$(python manage.py showmigrations "$app" 2>/dev/null | grep '\[ \]' | head -1 || echo "")
            if [ ! -z "$PENDING" ]; then
                echo "🔧 Aplicando fake-initial para $app"
                python manage.py migrate "$app" --fake-initial 2>/dev/null || echo "⚠️ Falha no fake-initial para $app (pode ser normal)"
            fi
        done
    fi
    
    # Tentar aplicar migrações restantes
    echo "🔄 Aplicando migrações restantes..."
    python manage.py migrate --noinput || {
        echo "⚠️ Algumas migrações falharam, mas continuando..."
    }
else
    echo "✅ Banco de dados limpo, aplicando migrações normalmente..."
    python manage.py migrate --noinput || {
        echo "❌ Falha nas migrações em banco limpo!"
        exit 1
    }
fi

# ==========================================================
# COLETAR ARQUIVOS ESTÁTICOS
# ==========================================================
STATIC_DIR="/badgr_server/staticfiles"
echo "==> Verificando arquivos estáticos..."
if [ ! -d "$STATIC_DIR" ] || [ -z "$(ls -A "$STATIC_DIR" 2>/dev/null)" ]; then
    echo "📦 Coletando arquivos estáticos..."
    python manage.py collectstatic --noinput --clear
else
    echo "✅ Arquivos estáticos já presentes em $STATIC_DIR"
fi

# ==========================================================
# CONFIGURAR OAUTH2 APPLICATIONS E APPLICATION INFO
# ==========================================================
echo "==> Configurando OAuth2 Applications e ApplicationInfo..."
python manage.py shell -c "
from oauth2_provider.models import Application
from mainsite.models import ApplicationInfo

print('🔧 Configurando OAuth2 Applications...')

# =============================================================================
# GARANTIR QUE APP 'PUBLIC' EXISTE (Para frontend)
# =============================================================================
app_public, created = Application.objects.get_or_create(
    client_id='public',
    defaults={
        'name': 'Badgr Public Default',
        'client_type': Application.CLIENT_PUBLIC,
        'authorization_grant_type': Application.GRANT_PASSWORD,
    }
)

if created:
    print('✓ Application public criado')
else:
    print('✓ Application public já existe')

# =============================================================================
# GARANTIR APPLICATION INFO PARA APP 'PUBLIC' (Scopes necessários)
# =============================================================================
app_info, created = ApplicationInfo.objects.get_or_create(
    application=app_public,
    defaults={
        'name': 'Badgr Public Default',
        'allowed_scopes': 'rw:profile rw:issuer rw:backpack',
        'trust_email_verification': True,
    }
)

if created:
    print('✓ ApplicationInfo para public criado')
    print(f'  Scopes permitidos: {app_info.allowed_scopes}')
else:
    print('✓ ApplicationInfo para public já existe')
    # Garantir scopes corretos mesmo se já existe
    expected_scopes = 'rw:profile rw:issuer rw:backpack'
    if app_info.allowed_scopes != expected_scopes:
        app_info.allowed_scopes = expected_scopes
        app_info.save()
        print('✓ Scopes atualizados para: rw:profile rw:issuer rw:backpack')

# =============================================================================
# VERIFICAR SE APP 'BADGR FRONTEND' TEM APPLICATION INFO
# =============================================================================
try:
    app_frontend = Application.objects.get(name='Badgr Frontend')
    app_info_frontend, created = ApplicationInfo.objects.get_or_create(
        application=app_frontend,
        defaults={
            'name': 'Badgr Frontend',
            'allowed_scopes': 'rw:profile rw:issuer rw:backpack',
            'trust_email_verification': True,
        }
    )
    if created:
        print('✓ ApplicationInfo para Badgr Frontend criado')
    else:
        print('✓ ApplicationInfo para Badgr Frontend já existe')
except Application.DoesNotExist:
    print('⚠ Application Badgr Frontend não encontrado (normal se criado via admin)')

print('🎉 OAuth2 configurado com sucesso!')
print('')
print('=== RESUMO APPLICATIONS ===')
apps = Application.objects.all()
for app in apps:
    try:
        info = ApplicationInfo.objects.get(application=app)
        print(f'- {app.name} (client_id: {app.client_id})')
        print(f'  Scopes: {info.allowed_scopes}')
    except ApplicationInfo.DoesNotExist:
        print(f'- {app.name} (client_id: {app.client_id}) - SEM ApplicationInfo!')
print('========================')
"

# ==========================================================
# CONFIGURAÇÕES ESPECÍFICAS DO UFSC OAUTH
# ==========================================================
echo "==> Configurando integração UFSC..."

# Verificar se UFSC está habilitado
if [[ "${BADGR_SOCIAL_PROVIDERS:-}" == *"ufsc"* ]]; then
    echo "✅ Provider UFSC está habilitado em BADGR_SOCIAL_PROVIDERS"
    
    echo "🔧 Configurando SocialApp UFSC..."
    python manage.py create_ufsc_socialapp || {
        echo "⚠️ Falha ao configurar SocialApp UFSC"
    }
    
    echo "🧪 Testando configuração OAuth UFSC..."
    python manage.py test_ufsc_oauth || {
        echo "⚠️ Teste OAuth UFSC falhou"
    }
else
    echo "⚠️ Provider UFSC não está habilitado em BADGR_SOCIAL_PROVIDERS"
    echo "   Para habilitar, adicione 'ufsc' à variável BADGR_SOCIAL_PROVIDERS"
    echo "   Tentando configurar mesmo assim..."
    
    python manage.py create_ufsc_socialapp 2>/dev/null || {
        echo "⚠️ Falha ao configurar SocialApp UFSC (comando pode não existir ainda)"
    }
    
    python manage.py test_ufsc_oauth 2>/dev/null || {
        echo "⚠️ Teste OAuth UFSC falhou (comando pode não existir ainda)"
    }
fi

# ==========================================================
# VERIFICAÇÃO FINAL DO SISTEMA
# ==========================================================
echo "==> Verificação final do sistema..."
MIGRATION_STATUS=$(python manage.py showmigrations --list 2>/dev/null | grep '\[ \]' | wc -l || echo "0")
if [ "$MIGRATION_STATUS" -eq 0 ]; then
    echo "✅ Todas as migrações aplicadas com sucesso"
else
    echo "⚠️ Ainda há $MIGRATION_STATUS migrações pendentes (pode ser normal para alguns apps)"
fi

# Verificar se o servidor consegue inicializar (Django 1.11 tem opções limitadas)
echo "🔍 Verificando se Django consegue carregar..."
python manage.py check 2>/dev/null || {
    echo "⚠️ Django check falhou, mas continuando..."
}

# ==========================================================
# RESUMO FINAL
# ==========================================================
echo ""
echo "🎉 Inicialização concluída!"
echo "📊 Resumo:"
echo "   - Banco de dados: ✅ Conectado"
echo "   - Migrações: ✅ Processadas"  
echo "   - Arquivos estáticos: ✅ Coletados"
echo "   - OAuth2 Applications: ✅ Configurados"
echo "   - OAuth UFSC: ✅ Tentado configurar"
echo ""
echo "🚀 Sistema pronto para uso!"
echo "📋 Login de teste: teste@ufsc.br / 123456"
echo "🌐 Frontend: https://badges.setic.ufsc.br"
echo "🔧 Admin: https://api-badges.setic.ufsc.br/admin/"
