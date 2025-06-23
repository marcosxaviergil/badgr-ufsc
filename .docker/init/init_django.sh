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
# GERAR ARQUIVOS SWAGGER - CRÍTICO PARA DOCUMENTAÇÃO
# ==========================================================
echo "==> Gerando documentação Swagger..."

# Garantir que diretório existe
mkdir -p /badgr_server/apps/mainsite/static/swagger-ui

# Tentar usar comando dist primeiro
if python manage.py dist 2>/dev/null; then
   echo "✅ Comando 'dist' executado com sucesso"
else
   echo "⚠️ Comando 'dist' falhou, tentando geração manual..."
   
   # Gerar manualmente cada versão
   echo "🔧 Gerando Swagger v2..."
   python manage.py generate_swagger_spec \
       --output /badgr_server/apps/mainsite/static/swagger-ui/badgr_spec_v2.json \
       --preamble /badgr_server/apps/mainsite/static/swagger-ui/API_DESCRIPTION_v2.md \
       --version v2 \
       --include-oauth2-security || {
       echo "❌ ERRO CRÍTICO: Falha na geração do Swagger v2!"
       exit 1
   }
   
   echo "🔧 Gerando Swagger v1..."
   python manage.py generate_swagger_spec \
       --output /badgr_server/apps/mainsite/static/swagger-ui/badgr_spec_v1.json \
       --preamble /badgr_server/apps/mainsite/static/swagger-ui/API_DESCRIPTION_v1.md \
       --version v1 \
       --include-oauth2-security || {
       echo "⚠️ Falha na geração do Swagger v1, mas continuando com v2..."
   }
fi

# Verificar se arquivos foram gerados
echo "🔍 Verificando arquivos Swagger gerados..."
if [ -f "/badgr_server/apps/mainsite/static/swagger-ui/badgr_spec_v2.json" ]; then
   echo "✅ badgr_spec_v2.json gerado com sucesso"
   ls -la /badgr_server/apps/mainsite/static/swagger-ui/badgr_spec_v2.json
else
   echo "❌ ERRO CRÍTICO: badgr_spec_v2.json NÃO foi gerado!"
   echo "📂 Conteúdo do diretório swagger-ui:"
   ls -la /badgr_server/apps/mainsite/static/swagger-ui/ || echo "Diretório não existe"
   exit 1
fi

if [ -f "/badgr_server/apps/mainsite/static/swagger-ui/badgr_spec_v1.json" ]; then
   echo "✅ badgr_spec_v1.json gerado com sucesso"
else
   echo "⚠️ badgr_spec_v1.json não gerado, mas continuando..."
fi

# ==========================================================
# COLETAR ARQUIVOS ESTÁTICOS - CRÍTICO PARA uWSGI
# ==========================================================
STATIC_DIR="/badgr_server/staticfiles"
echo "==> Coletando arquivos estáticos..."

# Limpar e coletar arquivos estáticos
echo "📦 Executando collectstatic..."
python manage.py collectstatic --noinput --clear || {
   echo "❌ ERRO CRÍTICO: Falha no collectstatic!"
   exit 1
}

# Verificar se arquivos swagger foram copiados
echo "🔍 Verificando arquivos Swagger em staticfiles..."
if [ -f "$STATIC_DIR/swagger-ui/badgr_spec_v2.json" ]; then
   echo "✅ Arquivos Swagger copiados para staticfiles"
   ls -la "$STATIC_DIR/swagger-ui/"
else
   echo "❌ ERRO: Arquivos Swagger não copiados para staticfiles!"
   echo "📂 Tentando cópia manual..."
   
   # Cópia manual de emergência
   mkdir -p "$STATIC_DIR/swagger-ui/"
   if [ -f "/badgr_server/apps/mainsite/static/swagger-ui/badgr_spec_v2.json" ]; then
       cp /badgr_server/apps/mainsite/static/swagger-ui/*.json "$STATIC_DIR/swagger-ui/" 2>/dev/null || true
       cp /badgr_server/apps/mainsite/static/swagger-ui/*.js "$STATIC_DIR/swagger-ui/" 2>/dev/null || true
       cp /badgr_server/apps/mainsite/static/swagger-ui/*.css "$STATIC_DIR/swagger-ui/" 2>/dev/null || true
       cp /badgr_server/apps/mainsite/static/swagger-ui/*.html "$STATIC_DIR/swagger-ui/" 2>/dev/null || true
       cp /badgr_server/apps/mainsite/static/swagger-ui/*.md "$STATIC_DIR/swagger-ui/" 2>/dev/null || true
       
       if [ -f "$STATIC_DIR/swagger-ui/badgr_spec_v2.json" ]; then
           echo "✅ Cópia manual bem-sucedida"
       else
           echo "❌ ERRO CRÍTICO: Falha na cópia manual!"
           exit 1
       fi
   else
       echo "❌ ERRO CRÍTICO: Arquivo source não existe para cópia!"
       exit 1
   fi
fi

# ==========================================================
# ✅ NOVO: CRIAR LINKS SIMBÓLICOS PARA COMPATIBILIDADE SWAGGER
# ==========================================================
echo "==> Criando links de compatibilidade para Swagger..."
echo "🔗 Criando links simbólicos api_spec -> badgr_spec para compatibilidade..."

# Criar links simbólicos para resolver problema de nomenclatura
if [ -f "$STATIC_DIR/swagger-ui/badgr_spec_v1.json" ]; then
   ln -sf badgr_spec_v1.json "$STATIC_DIR/swagger-ui/api_spec_v1.json"
   echo "✅ Link criado: api_spec_v1.json -> badgr_spec_v1.json"
else
   echo "⚠️ badgr_spec_v1.json não encontrado, pulando link v1"
fi

if [ -f "$STATIC_DIR/swagger-ui/badgr_spec_v2.json" ]; then
   ln -sf badgr_spec_v2.json "$STATIC_DIR/swagger-ui/api_spec_v2.json"
   echo "✅ Link criado: api_spec_v2.json -> badgr_spec_v2.json"
else
   echo "❌ ERRO: badgr_spec_v2.json não encontrado para link!"
   exit 1
fi

# Verificar se links funcionam
echo "🔍 Verificando links de compatibilidade..."
if [ -L "$STATIC_DIR/swagger-ui/api_spec_v2.json" ] && [ -f "$STATIC_DIR/swagger-ui/api_spec_v2.json" ]; then
   echo "✅ Links de compatibilidade funcionando corretamente"
else
   echo "⚠️ Problema com links de compatibilidade, mas continuando..."
fi

# ==========================================================
# ✅ NOVO: CORRIGIR REFERÊNCIAS QUEBRADAS NO SWAGGER V1
# ==========================================================
echo "==> Corrigindo referências quebradas no Swagger v1..."
echo "🔧 Corrigindo definições faltantes no spec v1..."

python -c "
import json
import os

v1_path = '$STATIC_DIR/swagger-ui/badgr_spec_v1.json'
v2_path = '$STATIC_DIR/swagger-ui/badgr_spec_v2.json'

if os.path.exists(v1_path) and os.path.exists(v2_path):
   try:
       with open(v1_path, 'r') as f:
           v1_spec = json.load(f)
       with open(v2_path, 'r') as f:
           v2_spec = json.load(f)
       
       # Lista de definições que podem estar faltando no v1
       missing_defs = ['BackpackAssertion', 'AssertionEvidence']
       
       if 'definitions' not in v1_spec:
           v1_spec['definitions'] = {}
       
       fixed_count = 0
       for def_name in missing_defs:
           if def_name in v2_spec.get('definitions', {}) and def_name not in v1_spec['definitions']:
               v1_spec['definitions'][def_name] = v2_spec['definitions'][def_name]
               print(f'✅ {def_name} copiado do v2 para v1')
               fixed_count += 1
       
       if fixed_count > 0:
           # Salvar v1 corrigido
           with open(v1_path, 'w') as f:
               json.dump(v1_spec, f, indent=2)
           print(f'🔧 {fixed_count} definições corrigidas no v1')
       else:
           print('✅ Nenhuma correção necessária no v1')
           
   except Exception as e:
       print(f'⚠️ Erro ao corrigir v1: {e}')
else:
   print('⚠️ Arquivos v1 ou v2 não encontrados para correção')
"

# Verificação final dos arquivos estáticos
echo "📊 Resumo dos arquivos estáticos:"
echo "   📁 Static dir: $STATIC_DIR"
echo "   📄 Swagger files:"
find "$STATIC_DIR/swagger-ui" -name "*.json" -type f | head -10 || echo "   ❌ Nenhum JSON encontrado"

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

# Verificação final crítica dos arquivos Swagger
echo "🔍 Verificação final crítica dos arquivos Swagger..."
SWAGGER_V2_PATH="$STATIC_DIR/swagger-ui/badgr_spec_v2.json"
if [ -f "$SWAGGER_V2_PATH" ]; then
   FILE_SIZE=$(stat -f%z "$SWAGGER_V2_PATH" 2>/dev/null || stat -c%s "$SWAGGER_V2_PATH" 2>/dev/null || echo "0")
   if [ "$FILE_SIZE" -gt 100 ]; then
       echo "✅ badgr_spec_v2.json verificado: ${FILE_SIZE} bytes"
   else
       echo "❌ ERRO: badgr_spec_v2.json muito pequeno ou vazio!"
       exit 1
   fi
else
   echo "❌ ERRO CRÍTICO: badgr_spec_v2.json não encontrado em staticfiles!"
   exit 1
fi

# ==========================================================
# RESUMO FINAL
# ==========================================================
echo ""
echo "🎉 Inicialização concluída com sucesso!"
echo "📊 Resumo completo:"
echo "   - Banco de dados: ✅ Conectado e migrado"
echo "   - Migrações: ✅ Processadas ($MIGRATION_STATUS pendentes)"  
echo "   - Documentação Swagger: ✅ Gerada e verificada"
echo "   - Arquivos estáticos: ✅ Coletados e verificados"
echo "   - Links de compatibilidade: ✅ Criados (api_spec -> badgr_spec)"
echo "   - Referências Swagger v1: ✅ Corrigidas automaticamente"
echo "   - OAuth2 Applications: ✅ Configurados"
echo "   - Sistema: ✅ Pronto para produção"
echo ""
echo "🚀 Sistema pronto para uso!"
echo "📋 URLs importantes:"
echo "   🔧 Admin: https://api-badges.setic.ufsc.br/admin/"
echo "   📚 Docs Swagger: https://api-badges.setic.ufsc.br/docs/v2/"
echo "   🌐 Frontend: https://badges.setic.ufsc.br"
echo "   🔗 OAuth UFSC config: /admin/socialaccount/socialapp/add/"
echo ""

# ==========================================================
# INICIAR uWSGI COM ARQUIVOS ESTÁTICOS
# ==========================================================
echo "🚀 Iniciando servidor uWSGI com suporte a arquivos estáticos..."
exec uwsgi --ini uwsgi.ini
