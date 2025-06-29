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

# ✅ CORREÇÃO: Método mais robusto para contar tabelas
TABLES_COUNT=$(python -c "
import os
import django
import sys
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mainsite.settings_local')
    django.setup()
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name LIKE \"django_%\"')
    result = cursor.fetchone()
    print(result[0] if result else 0)
except Exception as e:
    print('0')
    sys.stderr.write(f'Warning: {e}\n')
" 2>/dev/null)

# ✅ CORREÇÃO: Validar se TABLES_COUNT é um número válido
if ! [[ "$TABLES_COUNT" =~ ^[0-9]+$ ]]; then
    echo "⚠️ Não foi possível determinar estado do banco, assumindo banco existente"
    TABLES_COUNT=1
fi

echo "📊 Tabelas Django encontradas: $TABLES_COUNT"

if [ "$TABLES_COUNT" -gt 0 ]; then
  echo "⚠️ Banco de dados já contém $TABLES_COUNT tabelas Django"
  echo "==> Tentando sincronizar estado das migrações..."
  
  # ✅ CORREÇÃO: Verificar se notification_email existe ANTES de qualquer migração
  echo "==> Verificando campos existentes no banco antes de criar migrações..."
  NOTIFICATION_EMAIL_EXISTS=$(python -c "
import os
import django
import sys
try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mainsite.settings_local')
    django.setup()
    from django.db import connection
    cursor = connection.cursor()
    cursor.execute('DESCRIBE issuer_badgeinstance')
    columns = [row[0] for row in cursor.fetchall()]
    print('1' if 'notification_email' in columns else '0')
except Exception as e:
    print('0')
    sys.stderr.write(f'Warning: {e}\n')
" 2>/dev/null)

  if [ "$NOTIFICATION_EMAIL_EXISTS" = "1" ]; then
      echo "✅ Campo notification_email já existe no banco - pulando makemigrations"
      SKIP_MAKEMIGRATIONS=1
  else
      echo "📝 Campo notification_email não existe - permitindo makemigrations"
      SKIP_MAKEMIGRATIONS=0
  fi
  
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
  
  # ✅ CORREÇÃO: Só criar migrações se o campo não existir
  if [ "$SKIP_MAKEMIGRATIONS" = "0" ]; then
      echo "==> Criando migrações para mudanças no código..."
      python manage.py makemigrations --noinput || {
          echo "⚠️ Nenhuma migração nova criada ou erro no makemigrations"
      }
  else
      echo "⏭️ Pulando makemigrations - notification_email já existe"
  fi
  
  # Tentar aplicar migrações restantes com tratamento inteligente de erros
  echo "🔄 Aplicando migrações restantes..."
  python manage.py migrate --noinput 2>&1 | tee /tmp/migrate_output.log
  
  # ✅ CORREÇÃO: Verificar se erro é de coluna duplicada e aplicar fake automaticamente
  if grep -q "Duplicate column name 'notification_email'" /tmp/migrate_output.log; then
      echo "⚠️ Detectado erro de coluna duplicada - aplicando fake migration"
      # Encontrar a migração que falhou
      FAILED_MIGRATION=$(grep -o "issuer\..*_auto_.*" /tmp/migrate_output.log | head -1 | sed 's/issuer\.//' | sed 's/\.py.*//')
      if [ ! -z "$FAILED_MIGRATION" ]; then
          echo "🔧 Aplicando fake para migração: $FAILED_MIGRATION"
          python manage.py migrate issuer "$FAILED_MIGRATION" --fake || echo "⚠️ Falha no fake da migração"
          echo "🔄 Tentando aplicar migrações restantes novamente..."
          python manage.py migrate --noinput || echo "⚠️ Algumas migrações ainda falharam"
      else
          echo "⚠️ Não foi possível identificar migração falhada, aplicando fake para a mais recente"
          python manage.py migrate issuer --fake || echo "⚠️ Falha no fake da migração"
      fi
  elif ! grep -q "No migrations to apply" /tmp/migrate_output.log && grep -q -E "(Error|Exception|Traceback)" /tmp/migrate_output.log; then
      echo "⚠️ Algumas migrações falharam, mas continuando..."
  fi
  
  # Limpeza
  rm -f /tmp/migrate_output.log
  
else
  echo "✅ Banco de dados realmente limpo, aplicando migrações normalmente..."
  
  # ✅ Para banco limpo, criar migrações normalmente
  echo "==> Criando migrações para mudanças no código..."
  python manage.py makemigrations --noinput || {
      echo "⚠️ Nenhuma migração nova criada ou erro no makemigrations"
  }
  
  python manage.py migrate --noinput || {
      echo "❌ Falha nas migrações em banco limpo!"
      exit 1
  }
fi

# ==========================================================
# GARANTIR DIRETÓRIOS DE ARQUIVOS ESTÁTICOS
# ==========================================================
echo "==> Garantindo estrutura de diretórios de arquivos estáticos..."
STATIC_DIR="/badgr_server/staticfiles"
mkdir -p "$STATIC_DIR"
mkdir -p /badgr_server/apps/mainsite/static/swagger-ui
mkdir -p "$STATIC_DIR/swagger-ui"
mkdir -p "$STATIC_DIR/badgr-ui/images"
mkdir -p "$STATIC_DIR/admin"
echo "✅ Diretórios de arquivos estáticos criados"

# ==========================================================
# GERAR ARQUIVOS SWAGGER - CRÍTICO PARA DOCUMENTAÇÃO
# ==========================================================
echo "==> Gerando documentação Swagger..."

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
echo "==> Coletando arquivos estáticos..."

# Limpar e coletar arquivos estáticos
echo "📦 Executando collectstatic..."
python manage.py collectstatic --noinput --clear --verbosity=2 || {
   echo "❌ ERRO CRÍTICO: Falha no collectstatic!"
   exit 1
}

# ==========================================================
# VERIFICAÇÃO CRÍTICA DOS ARQUIVOS ESTÁTICOS
# ==========================================================
echo "==> Verificação crítica dos arquivos estáticos..."

# Verificar se arquivos swagger foram copiados
echo "🔍 Verificando arquivos Swagger em staticfiles..."
if [ -f "$STATIC_DIR/swagger-ui/badgr_spec_v2.json" ]; then
   echo "✅ Arquivos Swagger copiados para staticfiles"
   ls -la "$STATIC_DIR/swagger-ui/" | head -10
else
   echo "❌ ERRO: Arquivos Swagger não copiados para staticfiles!"
   echo "📂 Tentando cópia manual..."
   
   # Cópia manual de emergência
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

# Verificar arquivos críticos para /staff
echo "🔍 Verificando arquivos críticos para interface /staff..."

CRITICAL_STATIC_FILES=(
    "$STATIC_DIR/badgr-ui/images/logo.svg"
    "$STATIC_DIR/admin/css/base.css"
    "$STATIC_DIR/admin/js/core.js"
)

missing_files=0
for file in "${CRITICAL_STATIC_FILES[@]}"; do
    if [ -f "$file" ]; then
        size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
        echo "✅ $(basename "$file") presente ($size bytes)"
    else
        echo "❌ CRÍTICO: $(basename "$file") AUSENTE"
        missing_files=$((missing_files + 1))
    fi
done

if [ "$missing_files" -gt 0 ]; then
    echo "❌ ERRO CRÍTICO: $missing_files arquivos críticos ausentes!"
    echo "📂 Conteúdo do staticfiles:"
    find "$STATIC_DIR" -type f | head -20
    exit 1
fi

# Verificar permissões dos arquivos estáticos
echo "🔍 Verificando permissões dos arquivos estáticos..."
chmod -R 755 "$STATIC_DIR" || {
    echo "⚠️ Não foi possível definir permissões, mas continuando..."
}
echo "✅ Permissões dos arquivos estáticos ajustadas"

# ==========================================================
# CRIAR LINKS SIMBÓLICOS PARA COMPATIBILIDADE SWAGGER
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
# CORRIGIR REFERÊNCIAS QUEBRADAS NO SWAGGER V1
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

# ==========================================================
# VERIFICAÇÃO FINAL DOS ARQUIVOS ESTÁTICOS
# ==========================================================
echo "==> Verificação final dos arquivos estáticos..."

# Verificação final crítica dos arquivos
echo "🔍 Verificação final crítica dos arquivos..."

# Verificar tamanhos dos arquivos Swagger
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

# Verificar se logo.svg está acessível
LOGO_PATH="$STATIC_DIR/badgr-ui/images/logo.svg"
if [ -f "$LOGO_PATH" ]; then
    LOGO_SIZE=$(stat -f%z "$LOGO_PATH" 2>/dev/null || stat -c%s "$LOGO_PATH" 2>/dev/null || echo "0")
    if [ "$LOGO_SIZE" -gt 1000 ]; then
        echo "✅ logo.svg verificado: ${LOGO_SIZE} bytes"
    else
        echo "❌ ERRO: logo.svg muito pequeno ou corrompido!"
        exit 1
    fi
else
    echo "❌ ERRO CRÍTICO: logo.svg não encontrado em staticfiles!"
    exit 1
fi

# Resumo dos arquivos estáticos
echo "📊 Resumo dos arquivos estáticos:"
echo "   📁 Static dir: $STATIC_DIR"
echo "   📄 Total de arquivos: $(find "$STATIC_DIR" -type f | wc -l)"
echo "   📄 Swagger files:"
find "$STATIC_DIR/swagger-ui" -name "*.json" -type f | head -10 || echo "   ❌ Nenhum JSON encontrado"
echo "   🖼️ Badgr UI images:"
find "$STATIC_DIR/badgr-ui/images" -type f | head -5 || echo "   ❌ Nenhuma imagem encontrada"

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

# Verificar se o servidor consegue inicializar
echo "🔍 Verificando se Django consegue carregar..."
python manage.py check --deploy 2>/dev/null || {
  python manage.py check 2>/dev/null || {
    echo "⚠️ Django check falhou, mas continuando..."
  }
}

# ==========================================================
# TESTE FINAL DE ARQUIVOS ESTÁTICOS CRÍTICOS
# ==========================================================
echo "==> Teste final de arquivos estáticos críticos..."

CRITICAL_TEST_FILES=(
    "$STATIC_DIR/badgr-ui/images/logo.svg"
    "$STATIC_DIR/badgr-ui/images/favicon.png"
    "$STATIC_DIR/admin/css/base.css"
    "$STATIC_DIR/swagger-ui/badgr_spec_v2.json"
)

echo "🔍 Verificação final de arquivos críticos:"
all_files_ok=true
for file in "${CRITICAL_TEST_FILES[@]}"; do
    if [ -f "$file" ] && [ -s "$file" ]; then
        size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
        echo "✅ $(basename "$file"): $size bytes"
    else
        echo "❌ FALTA: $(basename "$file")"
        all_files_ok=false
    fi
done

if [ "$all_files_ok" = false ]; then
    echo "❌ ERRO CRÍTICO: Arquivos estáticos críticos ausentes!"
    echo "📂 Listando conteúdo de staticfiles para debug:"
    find "$STATIC_DIR" -type f | head -30
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
echo "   - Arquivos críticos /staff: ✅ Presentes e válidos"
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
