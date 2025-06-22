# Badgr Server
PT-BR: *Gerenciamento de badges digitais para emissores, conquistadores e consumidores*  
EN-US: *Digital badge management for issuers, earners, and consumers*  
ES-ES: *Gestión de insignias digitales para emisores, ganadores y consumidores*  
DE-DE: *Digitale Abzeichenverwaltung für Aussteller, Empfänger und Verbraucher*

PT-BR: Badgr-server é o backend Python/Django para emissão de [Open Badges](http://openbadges.org). Além de uma poderosa API para emissores e uma interface web para emissão, o Badgr oferece gerenciamento integrado e compartilhamento de badges para os conquistadores. Contas gratuitas são hospedadas pela Concentric Sky em [Badgr.com](http://info.badgr.com), mas para controle total do seu próprio ambiente de emissão, o Badgr Server está disponível como open source em Python/Django.

EN-US: Badgr-server is the Python/Django API backend for issuing [Open Badges](http://openbadges.org). In addition to a powerful Issuer API and browser-based user interface for issuing, Badgr offers integrated badge management and sharing for badge earners. Free accounts are hosted by Concentric Sky at [Badgr.com](http://info.badgr.com), but for complete control over your own issuing environment, Badgr Server is available open source as a Python/Django application.

ES-ES: Badgr-server es el backend Python/Django para la emisión de [Open Badges](http://openbadges.org). Además de una potente API para emisores y una interfaz web para emitir, Badgr ofrece gestión y compartición de insignias para los ganadores. Las cuentas gratuitas son alojadas por Concentric Sky en [Badgr.com](http://info.badgr.com), pero para control total de tu propio entorno de emisión, Badgr Server está disponible como una aplicación de código abierto en Python/Django.

DE-DE: Badgr-server ist das Python/Django-API-Backend für die Ausstellung von [Open Badges](http://openbadges.org). Zusätzlich zu einer leistungsfähigen Aussteller-API und einer browserbasierten Benutzeroberfläche für die Ausstellung bietet Badgr integriertes Abzeichenmanagement und -freigabe für Empfänger. Kostenlose Konten werden von Concentric Sky bei [Badgr.com](http://info.badgr.com) gehostet, aber für vollständige Kontrolle über Ihre eigene Ausstellungsumgebung ist Badgr Server als Open-Source-Python/Django-Anwendung verfügbar.

Veja também [badgr-ui](https://github.com/concentricsky/badgr-ui), o frontend Angular que serve como interface do usuário para este projeto.

See also [badgr-ui](https://github.com/concentricsky/badgr-ui), the Angular front end that serves as users' interface for this project.

Consulta también [badgr-ui](https://github.com/concentricsky/badgr-ui), la interfaz frontend Angular para este proyecto.

Siehe auch [badgr-ui](https://github.com/concentricsky/badgr-ui), das Angular-Frontend, das als Benutzeroberfläche für dieses Projekt dient.

### Sobre o Projeto Badgr
PT-BR: Badgr foi desenvolvido pela [Concentric Sky](https://concentricsky.com), a partir de 2015, como implementação open source de referência para a especificação Open Badges. Ele permite emitir badges portáteis e verificáveis, bem como permitir que os usuários gerenciem badges recebidos de qualquer emissor usando este padrão de dados abertos. Desde 2015, o Badgr tem sido utilizado por centenas de instituições de ensino e outras organizações no mundo todo. Veja a [Página do Projeto](https://badgr.org) para mais detalhes sobre contribuição e integração.

EN-US: Badgr was developed by [Concentric Sky](https://concentricsky.com), starting in 2015 to serve as an open source reference implementation of the Open Badges Specification. It provides functionality to issue portable, verifiable Open Badges as well as to allow users to manage badges they have been awarded by any issuer that uses this open data standard. Since 2015, Badgr has grown to be used by hundreds of educational institutions and other people and organizations worldwide. See [Project Homepage](https://badgr.org) for more details about contributing to and integrating with Badgr.

ES-ES: Badgr fue desarrollado por [Concentric Sky](https://concentricsky.com) a partir de 2015 como una implementación de referencia de código abierto de la Especificación Open Badges. Proporciona funcionalidad para emitir insignias portátiles y verificables, así como para permitir a los usuarios administrar las insignias que han recibido de cualquier emisor que utilice este estándar de datos abiertos. Desde 2015, Badgr ha sido utilizado por cientos de instituciones educativas y otras organizaciones en todo el mundo. Consulta la [Página del Proyecto](https://badgr.org) para obtener más detalles sobre cómo contribuir e integrarse con Badgr.

DE-DE: Badgr wurde von [Concentric Sky](https://concentricsky.com) ab 2015 als Open-Source-Referenzimplementierung der Open Badges Specification entwickelt. Es bietet Funktionen zum Ausstellen tragbarer, überprüfbarer Open Badges sowie zur Verwaltung von Abzeichen, die Benutzer von jedem Aussteller erhalten haben, der diesen offenen Datenstandard verwendet. Seit 2015 wird Badgr von Hunderten Bildungseinrichtungen und anderen Organisationen weltweit genutzt. Siehe [Projektseite](https://badgr.org) für weitere Informationen über Beiträge und Integration mit Badgr.

---

## Como começar o desenvolvimento local.
PT-BR: Pré-requisitos:  
EN-US: Prerequisites:  
ES-ES: Requisitos previos:  
DE-DE: Voraussetzungen:  

* PT-BR: Instale o docker (veja [instruções](https://docs.docker.com/install/))
* EN-US: Install docker (see [instructions](https://docs.docker.com/install/))
* ES-ES: Instala docker (ver [instrucciones](https://docs.docker.com/install/))
* DE-DE: Installieren Sie Docker (siehe [Anleitung](https://docs.docker.com/install/))

### Copie o arquivo de configuração de exemplo local

PT-BR: Copie o exemplo de configuração para desenvolvimento:  
EN-US: Copy the example development settings:  
ES-ES: Copia el archivo de configuración de desarrollo de ejemplo:  
DE-DE: Kopieren Sie die Beispiel-Entwicklungskonfiguration:  

* `cp .docker/etc/settings_local.dev.py.example .docker/etc/settings_local.dev.py`
    
PT-BR: **NOTA**: você *pode* querer copiar e editar a configuração de produção. Veja a seção "Executando o Django Server em Produção" abaixo para mais detalhes.  
EN-US: **NOTE**: you *may* wish to copy and edit the production config. See Running the Django Server in "Production" below for more details.  
ES-ES: **NOTA**: *puede* que desees copiar y editar la configuración de producción. Consulta la sección de ejecución en "Producción" más abajo para más detalles.  
DE-DE: **HINWEIS**: Es *kann* sinnvoll sein, die Produktionskonfiguration zu kopieren und zu bearbeiten. Siehe unten unter "Ausführen des Django-Servers in der Produktion" für weitere Details.

* `cp .docker/etc/settings_local.prod.py.example .docker/etc/settings_local.prod.py`

### Personalize a configuração local conforme seu ambiente

PT-BR: Edite os arquivos `settings_local.dev.py` e/ou `settings_local.prod.py` para ajustar as seguintes configurações:  
EN-US: Edit the `settings_local.dev.py` and/or `settings_local.prod.py` to adjust the following settings:  
ES-ES: Edita los archivos `settings_local.dev.py` y/o `settings_local.prod.py` para ajustar las siguientes configuraciones:  
DE-DE: Bearbeiten Sie die Dateien `settings_local.dev.py` und/oder `settings_local.prod.py`, um die folgenden Einstellungen anzupassen:  

* PT-BR: Defina `DEFAULT_FROM_EMAIL` para um endereço, por exemplo `"noreply@localhost"`  
  EN-US: Set `DEFAULT_FROM_EMAIL` to an address, for instance `"noreply@localhost"`  
  ES-ES: Define `DEFAULT_FROM_EMAIL` a una dirección, por ejemplo `"noreply@localhost"`  
  DE-DE: Setzen Sie `DEFAULT_FROM_EMAIL` auf eine Adresse, z. B. `"noreply@localhost"`  
    * PT-BR: O padrão `EMAIL_BACKEND= 'django.core.mail.backends.console.EmailBackend'` exibirá o conteúdo do email no console, geralmente suficiente para desenvolvimento. Outras opções estão disponíveis. Veja a documentação do Django sobre [envio de email](https://docs.djangoproject.com/en/1.11/topics/email/).  
    * EN-US: The default `EMAIL_BACKEND= 'django.core.mail.backends.console.EmailBackend'` will log email content to console, which is often adequate for development. Other options are available. See Django docs for [sending email](https://docs.djangoproject.com/en/1.11/topics/email/).  
    * ES-ES: El valor por defecto `EMAIL_BACKEND= 'django.core.mail.backends.console.EmailBackend'` mostrará el contenido del correo en la consola, lo que suele ser suficiente para desarrollo. Hay otras opciones disponibles. Consulta la documentación de Django sobre [envío de emails](https://docs.djangoproject.com/en/1.11/topics/email/).  
    * DE-DE: Die Standardeinstellung `EMAIL_BACKEND= 'django.core.mail.backends.console.EmailBackend'` zeigt den E-Mail-Inhalt in der Konsole an, was für die Entwicklung oft ausreicht. Weitere Optionen sind verfügbar. Siehe Django-Dokumentation zum [Versenden von E-Mails](https://docs.djangoproject.com/en/1.11/topics/email/).  

* PT-BR: Defina `SECRET_KEY` e `UNSUBSCRIBE_SECRET_KEY` como valores aleatórios criptograficamente seguros e diferentes.  
  EN-US: Set `SECRET_KEY` and `UNSUBSCRIBE_SECRET_KEY` each to (different) cryptographically secure random values.  
  ES-ES: Define `SECRET_KEY` y `UNSUBSCRIBE_SECRET_KEY` a valores aleatorios y seguros.  
  DE-DE: Setzen Sie `SECRET_KEY` und `UNSUBSCRIBE_SECRET_KEY` auf (verschiedene) kryptografisch sichere Zufallswerte.  
    * PT-BR: Gere valores com: `python -c "import base64; import os; print(base64.b64encode(os.urandom(30)).decode('utf-8'))"`  
    * EN-US: Generate values with: `python -c "import base64; import os; print(base64.b64encode(os.urandom(30)).decode('utf-8'))"`  
    * ES-ES: Genera valores con: `python -c "import base64; import os; print(base64.b64encode(os.urandom(30)).decode('utf-8'))"`  
    * DE-DE: Generieren Sie Werte mit: `python -c "import base64; import os; print(base64.b64encode(os.urandom(30)).decode('utf-8'))"`  

* PT-BR: Defina `AUTHCODE_SECRET_KEY` como uma string base64 segura de 32 bytes.  
  EN-US: Set `AUTHCODE_SECRET_KEY` to a 32 byte url-safe base64-encoded random string. This key is used for symmetrical encryption of authentication tokens. If not defined, services like OAuth will not work.  
  ES-ES: Define `AUTHCODE_SECRET_KEY` como una cadena base64 de 32 bytes segura.  
  DE-DE: Setzen Sie `AUTHCODE_SECRET_KEY` auf einen 32-Byte-url-sicheren base64-codierten Zufallswert.  
    * PT-BR: Gere um valor com: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"`  
    * EN-US: Generate a value with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"`  
    * ES-ES: Genera un valor con: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"`  
    * DE-DE: Generieren Sie einen Wert mit: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"`  

#### Outras opções de configuração

PT-BR: Ajuste os valores abaixo em seus arquivos de configuração para adequar a aplicação ao seu uso:  
EN-US: Set or adjust these values in your `settings_local.dev.py` and/or `settings_local.prod.py` file to further configure the application to your specific needs.  
ES-ES: Ajusta los siguientes valores en tus archivos de configuración para adecuar la aplicación a tus necesidades.  
DE-DE: Passen Sie die folgenden Werte in Ihren Konfigurationsdateien an, um die Anwendung weiter zu konfigurieren:  

* PT-BR: `HELP_EMAIL`: Um endereço de email do suporte. O padrão é `help@badgr.io`.  
  EN-US: `HELP_EMAIL`: An email address for your support staff. The default is `help@badgr.io`.  
  ES-ES: `HELP_EMAIL`: Una dirección de email para el soporte. El valor por defecto es `help@badgr.io`.  
  DE-DE: `HELP_EMAIL`: Eine E-Mail-Adresse für Ihren Support. Der Standardwert ist `help@badgr.io`.  

* PT-BR: `BADGR_APPROVED_ISSUERS_ONLY`: Se definido como `True`, novos usuários não poderão criar novos emissores (apenas ser adicionados como staff em emissores existentes), a menos que tenham a permissão Django `issuer.add_issuer`. O recomendado é criar um grupo com este privilégio via área `/staff` e adicionar os usuários apropriados ao grupo.  
  EN-US: `BADGR_APPROVED_ISSUERS_ONLY`: If you choose to set this value to `True`, new user accounts will not be able to define new issuers (though they can be added as staff on issuers defined by others) unless they have the Django user permission 'issuer.add_issuer'. The recommended way to grant users this privilege is to create a group that grants it in the `/staff` admin area and add the appropriate users to that group.  
  ES-ES: `BADGR_APPROVED_ISSUERS_ONLY`: Si defines este valor como `True`, los nuevos usuarios no podrán crear emisores (solo ser añadidos como staff), a menos que tengan el permiso `issuer.add_issuer`. Se recomienda crear un grupo con este permiso en el área de `/staff` y agregar a los usuarios correspondientes.  
  DE-DE: `BADGR_APPROVED_ISSUERS_ONLY`: Wenn Sie diesen Wert auf `True` setzen, können neue Benutzer keine neuen Aussteller anlegen (können aber als Mitarbeiter bei bestehenden hinzugefügt werden), es sei denn, sie haben die Django-Berechtigung `issuer.add_issuer`. Der empfohlene Weg ist, eine Gruppe mit dieser Berechtigung im `/staff` Admin-Bereich zu erstellen und die entsprechenden Benutzer hinzuzufügen.  

* PT-BR: `PINGDOM_MONITORING_ID`: Caso use o [Pingdom](https://www.pingdom.com/) para monitorar a performance do site, incluindo esta configuração irá adicionar o script de monitoramento no cabeçalho.  
  EN-US: `PINGDOM_MONITORING_ID`: If you use [Pingdom](https://www.pingdom.com/) to monitor site performance, including this setting will embed Pingdom tracking script into the header.  
  ES-ES: `PINGDOM_MONITORING_ID`: Si utilizas [Pingdom](https://www.pingdom.com/) para monitorizar el sitio, incluir esta configuración añadirá el script de monitorización al encabezado.  
  DE-DE: `PINGDOM_MONITORING_ID`: Wenn Sie [Pingdom](https://www.pingdom.com/) zur Überwachung der Website-Performance verwenden, wird durch diese Einstellung das Pingdom-Tracking-Skript im Header eingebettet.  

* PT-BR: `CELERY_ALWAYS_EAGER`: Ao definir como `True`, as tasks do Celery rodam de forma síncrona. Celery é um executor de tarefas assíncronas integrado ao Django e Badgr. Em ambientes de desenvolvimento, é seguro manter essa flag como `True`.  
  EN-US: `CELERY_ALWAYS_EAGER`: Setting this value to `True` causes Celery to immediately run tasks synchronously. Celery is an asynchronous task runner built into Django and Badgr. Advanced deployments may separate celery workers from web nodes for improved performance. For development environments where Celery tasks should run synchronously, set this flag to true. Very few time-intensive tasks are part of this repository, and eager is a safe setting for most production deploys.  
  ES-ES: `CELERY_ALWAYS_EAGER`: Si lo defines como `True`, las tareas de Celery se ejecutarán de forma síncrona. Celery es un gestor de tareas asíncronas integrado. En desarrollo, es seguro dejar esta opción activada.  
  DE-DE: `CELERY_ALWAYS_EAGER`: Wenn dieser Wert auf `True` gesetzt ist, werden Celery-Aufgaben synchron ausgeführt. Celery ist ein asynchroner Task-Runner, der in Django und Badgr integriert ist. Für Entwicklungsumgebungen, in denen Celery-Aufgaben synchron laufen sollen, setzen Sie diese Flag auf `True`.  

* PT-BR: `OPEN_FOR_SIGNUP`: Permite desabilitar o cadastro de novos usuários pela API ao definir para `False`. O padrão é `True`.  
  EN-US: `OPEN_FOR_SIGNUP`: Allows you to turn off signup through the API by setting to `False` if you would like to use Badgr for only single-account use or to manually create all users in `/staff`. The default is `True` (signup API is enabled). UX is not well-supported in the `/staff` interface.  
  ES-ES: `OPEN_FOR_SIGNUP`: Permite desactivar el registro a través de la API si se define como `False`. El valor por defecto es `True`.  
  DE-DE: `OPEN_FOR_SIGNUP`: Ermöglicht es Ihnen, die Anmeldung über die API zu deaktivieren, indem Sie sie auf `False` setzen. Standardmäßig ist `True`.  

* PT-BR: `DEFAULT_FILE_STORAGE` e `MEDIA_URL`: Django suporta diferentes backends para armazenar arquivos, conforme sua estratégia de implantação. Veja a documentação Django sobre a [API de armazenamento de arquivos](https://docs.djangoproject.com/en/1.11/ref/files/storage/)  
  EN-US: `DEFAULT_FILE_STORAGE` and `MEDIA_URL`: Django supports various backends for storing media, as applicable for your deployment strategy. See Django docs on the [file storage API](https://docs.djangoproject.com/en/1.11/ref/files/storage/)  
  ES-ES: `DEFAULT_FILE_STORAGE` y `MEDIA_URL`: Django admite varios backends para almacenar archivos. Consulta la documentación sobre la [API de almacenamiento de archivos](https://docs.djangoproject.com/en/1.11/ref/files/storage/)  
  DE-DE: `DEFAULT_FILE_STORAGE` und `MEDIA_URL`: Django unterstützt verschiedene Backends für die Speicherung von Dateien. Siehe Django-Dokumentation zur [Dateispeicher-API](https://docs.djangoproject.com/en/1.11/ref/files/storage/)  

---

### Executando o Django Server em Desenvolvimento

PT-BR: Para desenvolvimento, é melhor rodar o projeto com o servidor de desenvolvimento do django. O servidor recarrega automaticamente dentro do container docker ao modificar código em `apps/`.  
EN-US: For development, it is usually best to run the project with the builtin django development server. The development server will reload itself in the docker container whenever changes are made to the code in `apps/`.  
ES-ES: Para desarrollo, lo mejor es ejecutar el proyecto con el servidor de desarrollo de Django. El servidor se recargará automáticamente en el contenedor docker al modificar código en `apps/`.  
DE-DE: Für die Entwicklung ist es am besten, das Projekt mit dem eingebauten Django-Entwicklungsserver auszuführen. Der Entwicklungsserver wird im Docker-Container automatisch neu geladen, wenn Änderungen am Code in `apps/` vorgenommen werden.

PT-BR: Para rodar o projeto em modo desenvolvimento:  
EN-US: To run the project with docker in a development mode:  
ES-ES: Para ejecutar el proyecto en modo desarrollo:  
DE-DE: Um das Projekt im Entwicklungsmodus auszuführen:

* `docker-compose up`: PT-BR: constrói e inicia o django e demais componentes  
  EN-US: build and get django and other components running  
  ES-ES: construye y pone en marcha django y otros componentes  
  DE-DE: baut und startet django und andere Komponenten

* `docker-compose exec api python /badgr_server/manage.py migrate` - PT-BR: (com docker rodando) cria tabelas no banco  
  EN-US: (while running) set up database tables  
  ES-ES: (con docker en marcha) crea las tablas de la base de datos  
  DE-DE: (während läuft) Datenbanktabellen einrichten

* `docker-compose exec api python /badgr_server/manage.py collectstatic` - PT-BR: coloca os assets da UI na pasta estática  
  EN-US: Put built front-end assets into the static directory (Admin panel CSS, swagger docs).  
  ES-ES: Coloca los assets del frontend en la carpeta estática  
  DE-DE: Legt die gebauten Frontend-Assets im statischen Verzeichnis ab

* `docker-compose exec api python /badgr_server/manage.py createsuperuser` - PT-BR: siga as instruções para criar seu primeiro usuário admin  
  EN-US: follow prompts to create your first admin user account  
  ES-ES: sigue las instrucciones para crear tu primer usuario administrador  
  DE-DE: folgen Sie den Anweisungen, um Ihren ersten Admin-Benutzer zu erstellen

---

### Executando o Django Server em "Produção"

PT-BR: Por padrão, o `docker-compose` procura pelo arquivo `docker-compose.yml`. Este é o modo de desenvolvimento e padrão do projeto.  
EN-US: By default `docker-compose` will look for a `docker-compose.yml` for instructions of what to do. This file is the development (and thus default) config for `docker-compose`.  
ES-ES: Por defecto, `docker-compose` busca el archivo `docker-compose.yml`. Este archivo es la configuración por defecto y de desarrollo.  
DE-DE: Standardmäßig sucht `docker-compose` nach einer `docker-compose.yml` für Anweisungen. Diese Datei ist die Entwicklungs- und Standardkonfiguration.

PT-BR: Para rodar em modo produção, utilize o arquivo `docker-compose.prod.yml`, que copia o código para dentro do container e utiliza nginx e uwsgi:  
EN-US: If you'd like to run the project with a more production-like setup, you can specify the `docker-compose.prod.yml` file. This setup **copies** the project code in (instead of mirroring) and uses nginx with uwsgi to run django.  
ES-ES: Para correr en modo producción, usa `docker-compose.prod.yml`, que copia el código y usa nginx con uwsgi para ejecutar Django.  
DE-DE: Für Produktionsbetrieb benutzen Sie `docker-compose.prod.yml`, der den Code kopiert und nginx mit uwsgi verwendet.

* `docker-compose -f docker-compose.prod.yml up -d` - PT-BR: constrói e inicia django e componentes (modo produção)  
  EN-US: build and get django and other components (production mode)  
  ES-ES: construye y levanta django y otros componentes (modo producción)  
  DE-DE: baut und startet django und andere Komponenten (Produktionsmodus)

* `docker-compose -f docker-compose.prod.yml exec api python /badgr_server/manage.py migrate` - PT-BR: (com docker rodando) cria tabelas no banco  
  EN-US: (while running) set up database tables  
  ES-ES: (con docker en marcha) crea las tablas de la base de datos  
  DE-DE: (während läuft) Datenbanktabellen einrichten

PT-BR: Se estiver usando produção e fizer alterações que deseja ver no container rodando, pare e reconstrua os containers:  
EN-US: If you are using the production setup and you have made changes you wish to see reflected in the running container, you will need to stop and then rebuild the production containers:  
ES-ES: Si usas el entorno de producción y haces cambios, deberás parar y reconstruir los contenedores:  
DE-DE: Wenn Sie Änderungen vornehmen, stoppen und bauen Sie die Produktionscontainer neu:

* `docker-compose -f docker-compose.prod.yml build` - PT-BR: (re)constrói os containers de produção  
  EN-US: (re)build the production containers  
  ES-ES: (re)construye los contenedores de producción  
  DE-DE: (erneut) Produktionscontainer bauen

---

### Acessando o Django Server rodando no Docker

PT-BR: O servidor de desenvolvimento ficará acessível na porta `8000`:  
EN-US: The development server will be reachable on port `8000`:  
ES-ES: El servidor de desarrollo estará disponible en el puerto `8000`:  
DE-DE: Der Entwicklungsserver ist erreichbar unter Port `8000`:

* http://localhost:8000/ (desenvolvimento)  
* http://localhost:8000/ (development)  
* http://localhost:8000/ (desarrollo)  
* http://localhost:8000/ (Entwicklung)  

PT-BR: O servidor de produção estará acessível na porta `8080`:  
EN-US: The production server will be reachable on port `8080`:  
ES-ES: El servidor de producción estará disponible en el puerto `8080`:  
DE-DE: Der Produktionsserver ist erreichbar unter Port `8080`:

* http://localhost:8080/ (produção)  
* http://localhost:8080/ (production)  
* http://localhost:8080/ (producción)  
* http://localhost:8080/ (Produktion)  

PT-BR: Os exemplos de URL neste readme usam a porta de desenvolvimento. Ajuste se estiver em produção.  
EN-US: There are various examples of URLs in this readme and they all feature the development port. You will need to adjust that if you are using the production server.  
ES-ES: Los ejemplos de URL en este readme usan el puerto de desarrollo. Ajústalo si usas producción.  
DE-DE: Die URL-Beispiele in diesem Readme verwenden den Entwicklungsport. Passen Sie ihn ggf. an.

---

### Primeiro acesso

PT-BR:  
* Faça login em http://localhost:8000/staff/  
* Adicione um objeto `EmailAddress` para seu superusuário. [Edite seu super usuário](http://localhost:8000/staff/badgeuser/badgeuser/1/change/)  
* Adicione um objeto `TermsVersion` inicial  

EN-US:  
* Sign in to http://localhost:8000/staff/  
* Add an `EmailAddress` object for your superuser. [Edit your super user](http://localhost:8000/staff/badgeuser/badgeuser/1/change/)  
* Add an initial `TermsVersion` object  

ES-ES:  
* Inicia sesión en http://localhost:8000/staff/  
* Añade un objeto `EmailAddress` para tu superusuario. [Edita tu superusuario](http://localhost:8000/staff/badgeuser/badgeuser/1/change/)  
* Añade un objeto `TermsVersion` inicial  

DE-DE:  
* Melden Sie sich an unter http://localhost:8000/staff/  
* Fügen Sie ein `EmailAddress`-Objekt für Ihren Superuser hinzu. [Bearbeiten Sie Ihren Superuser](http://localhost:8000/staff/badgeuser/badgeuser/1/change/)  
* Fügen Sie ein erstes `TermsVersion`-Objekt hinzu  

---

#### Configuração do App Badgr

PT-BR:  
* Faça login em http://localhost:8000/staff  
* Acesse os registros "Badgr app" e crie um BadgrApp. Ele descreve a configuração do badgr-server para integrar com uma instalação do badgr-ui.

EN-US:  
* Sign in to http://localhost:8000/staff  
* View the "Badgr app" records and use the staff admin forms to create a BadgrApp. BadgrApp(s) describe the configuration that badgr-server needs to know about an associated installation of badgr-ui.

ES-ES:  
* Inicia sesión en http://localhost:8000/staff  
* Ve los registros de "Badgr app" y usa los formularios de admin para crear un BadgrApp.

DE-DE:  
* Melden Sie sich an unter http://localhost:8000/staff  
* Sehen Sie sich die "Badgr app"-Einträge an und verwenden Sie das Admin-Formular, um eine BadgrApp zu erstellen.

PT-BR: Se o [badgr-ui](https://github.com/concentricsky/badgr-ui) estiver rodando em http://localhost:4000, use:  
EN-US: If your [badgr-ui](https://github.com/concentricsky/badgr-ui) is running on http://localhost:4000, use the following values:  
ES-ES: Si tu [badgr-ui](https://github.com/concentricsky/badgr-ui) se ejecuta en http://localhost:4000, usa estos valores:  
DE-DE: Wenn Ihr [badgr-ui](https://github.com/concentricsky/badgr-ui) unter http://localhost:4000 läuft, verwenden Sie folgende Werte:

* CORS: PT-BR: `localhost:4000`
  EN-US: `localhost:4000`
  ES-ES: `localhost:4000`
  DE-DE: `localhost:4000`
* Signup redirect: PT-BR: `http://localhost:4000/signup/`
  EN-US: `http://localhost:4000/signup/`
  ES-ES: `http://localhost:4000/signup/`
  DE-DE: `http://localhost:4000/signup/`
* Email confirmation redirect: PT-BR: `http://localhost:4000/auth/login/`
  EN-US: `http://localhost:4000/auth/login/`
  ES-ES: `http://localhost:4000/auth/login/`
  DE-DE: `http://localhost:4000/auth/login/`
* Forgot password redirect: PT-BR: `http://localhost:4000/change-password/`
  EN-US: `http://localhost:4000/change-password/`
  ES-ES: `http://localhost:4000/change-password/`
  DE-DE: `http://localhost:4000/change-password/`
* UI login redirect: PT-BR: `http://localhost:4000/auth/login/`
  EN-US: `http://localhost:4000/auth/login/`
  ES-ES: `http://localhost:4000/auth/login/`
  DE-DE: `http://localhost:4000/auth/login/`
* UI signup success redirect: PT-BR: `http://localhost:4000/signup/success/`
  EN-US: `http://localhost:4000/signup/success/`
  ES-ES: `http://localhost:4000/signup/success/`
  DE-DE: `http://localhost:4000/signup/success/`
* UI connect success redirect: PT-BR: `http://localhost:4000/profile/`
  EN-US: `http://localhost:4000/profile/`
  ES-ES: `http://localhost:4000/profile/`
  DE-DE: `http://localhost:4000/profile/`
* Public pages redirect: PT-BR: `http://localhost:4000/public/`
  EN-US: `http://localhost:4000/public/`
  ES-ES: `http://localhost:4000/public/`
  DE-DE: `http://localhost:4000/public/`

---

#### Configuração de Autenticação

PT-BR:  
* [Crie um aplicativo OAuth2 Provider](http://localhost:8000/staff/oauth2_provider/application/add/) para o Badgr-UI usando:  
    * Client id: `public`
    * Client type: Público
    * allowed scopes: `rw:profile rw:issuer rw:backpack`
    * Authorization grant type: Resource owner password-based
    * Name: `Badgr UI`
    * Redirect uris: em branco

EN-US:  
* [Create an OAuth2 Provider Application](http://localhost:8000/staff/oauth2_provider/application/add/) for the Badgr-UI to use with  
    * Client id: `public`
    * Client type: Public
    * allowed scopes: `rw:profile rw:issuer rw:backpack`
    * Authorization grant type: Resource owner password-based
    * Name: `Badgr UI`
    * Redirect uris: blank

ES-ES:  
* [Crea una aplicación OAuth2 Provider](http://localhost:8000/staff/oauth2_provider/application/add/) para el Badgr-UI:  
    * Client id: `public`
    * Client type: Público
    * allowed scopes: `rw:profile rw:issuer rw:backpack`
    * Authorization grant type: Resource owner password-based
    * Name: `Badgr UI`
    * Redirect uris: en blanco

DE-DE:  
* [Erstellen Sie eine OAuth2-Provider-Anwendung](http://localhost:8000/staff/oauth2_provider/application/add/) für Badgr-UI mit:  
    * Client id: `public`
    * Client type: Public
    * allowed scopes: `rw:profile rw:issuer rw:backpack`
    * Authorization grant type: Resource owner password-based
    * Name: `Badgr UI`
    * Redirect uris: leer

---

### Instale e rode o Badgr UI {#badgr-ui}

PT-BR: Na pasta do seu projeto, clone o badgr-ui: `git clone https://github.com/concentricsky/badgr-ui.git badgr-ui`  
EN-US: Start in your `badgr` directory and clone badgr-ui source code: `git clone https://github.com/concentricsky/badgr-ui.git badgr-ui`  
ES-ES: En tu directorio badgr, clona el badgr-ui: `git clone https://github.com/concentricsky/badgr-ui.git badgr-ui`  
DE-DE: Wechseln Sie in Ihr badgr-Verzeichnis und klonen Sie badgr-ui: `git clone https://github.com/concentricsky/badgr-ui.git badgr-ui`

PT-BR: Para mais detalhes veja o Readme do [Badgr UI](https://github.com/concentricsky/badgr-ui).  
EN-US: For more details view the Readme for [Badgr UI](https://github.com/concentricsky/badgr-ui).  
ES-ES: Para más detalles consulta el Readme de [Badgr UI](https://github.com/concentricsky/badgr-ui).  
DE-DE: Für weitere Details siehe das Readme von [Badgr UI](https://github.com/concentricsky/badgr-ui).
