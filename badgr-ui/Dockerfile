# 🔧 Stage 1: Build da aplicação Angular
FROM node:11 AS builder

# Diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos do projeto Angular
COPY badgr-ui/ .

# Instala dependências
RUN npm install

# Compila a aplicação Angular (modo produção)
RUN npm run ng build --prod


# 🚀 Stage 2: Servir via NGINX com ferramentas úteis
FROM nginx:alpine AS runtime

# 🛠️ Instala ferramentas de debug úteis
RUN apk add --no-cache \
    nano \
    curl \
    bash \
    findutils \
    grep \
    coreutils \
    procps \
    less \
    tree \
    wget \
    net-tools

# 🔁 Copia a configuração personalizada do NGINX
COPY badgr-ui/nginx.conf /etc/nginx/nginx.conf

# 📦 Copia os arquivos compilados do Angular para o NGINX servir
COPY --from=builder /app/dist /usr/share/nginx/html

# 📁 Cria diretório para scripts ou inspeções futuras
RUN mkdir -p /scripts

# 🐚 Define bash como shell padrão
SHELL ["/bin/bash", "-c"]

# 🌐 Expõe a porta padrão do NGINX
EXPOSE 80
