# Zolkin Backend

**Zolkin** es una aplicación innovadora que permite gestionar *Gmail* y *Google Calendar* mediante lenguaje natural, utilizando un modelo de lenguaje de OpenAI y un sistema RAG (Retrieval-Augmented Generation) con *Milvus* como base de datos vectorial. Este backend, construido en *Python*, ofrece soporte para despliegue local y con *Docker*, integrando herramientas avanzadas para procesar documentos e imágenes. ¡Simplifica tu día a día con comandos naturales como "envía un correo" o "agenda una reunión"!

## Contenido

- [Características](#características)
- [Requisitos Previos](#requisitos-previos)
- [Instalación](#instalación)
- [Despliegue Local](#despliegue-local)
- [Despliegue con Docker](#despliegue-con-docker)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Componentes Principales](#componentes-principales)

## Características

- Gestión de *Gmail* y *Google Calendar* mediante lenguaje natural.
- Sistema RAG para recuperar información de documentos (PDFs, imágenes, etc.) usando *Milvus*.
- Integración de *Redis* para la memoria de chat durante las conversaciones.
- Conversión de documentos con *LibreOffice* y procesamiento de imágenes con *ImageMagick*.
- Uso de herramientas como *OCRmyPDF* y *PyMuPDF* para procesar PDFs.

## Requisitos Previos

Antes de empezar, asegúrate de tener instalado:
- [Git](https://git-scm.com/)
- [Python 3.12+](https://www.python.org/)
- [Docker](https://www.docker.com/)

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/jorge-jrzz/zolkin-backend
   cd zolkin-backend
   ```

## Despliegue Local

Sigue estos pasos para ejecutar Zolkin en tu máquina local:

### 1. Redis
Ejecuta un contenedor Redis para almacenar el historial de conversaciones:
```bash
docker run -d --name redis-stack-server -p 6379:6379 redis/redis-stack-server:latest
```
Más detalles en: [Install Redis Stack](https://redis.io/docs/latest/operate/oss_and_stack/install/install-stack/).

### 2. Milvus
Descarga y ejecuta Milvus como base de datos vectorial para el RAG:
```bash
curl -sfL https://raw.githubusercontent.com/milvus-io/milvus/master/scripts/standalone_embed.sh -o standalone_embed.sh
bash standalone_embed.sh start
```
Consulta: [Milvus Prerequisites](https://milvus.io/docs/prerequisite-docker.md).

### 3. OCRmyPDF
Instala OCRmyPDF según tu sistema operativo:
| Sistema Operativo           | Comando                   |
|-----------------------------|---------------------------|
| Debian, Ubuntu              | `apt install ocrmypdf`    |
| Windows (WSL)               | `apt install ocrmypdf`    |
| Fedora                      | `dnf install ocrmypdf`    |
| macOS (Homebrew)            | `brew install ocrmypdf`   |
Más opciones en: [OCRmyPDF Installation](https://ocrmypdf.readthedocs.io/en/latest/installation.html).

### 4. LibreOffice 
Instala LibreOffice para verificar el formato de los documentos para el RAG:
- Descarga e instala desde: [LibreOffice Installation](https://www.libreoffice.org/get-help/install-howto/).

### 5. ImageMagick
Instala ImageMagick para manejar imágenes en el RAG:
- Descarga desde: [ImageMagick Download](https://imagemagick.org/script/download.php).

### 6. Dependencias de Zolkin
Instala las dependencias de Python según tu gestor preferido:
| Gestor de Dependencias | Comando                          |
|------------------------|----------------------------------|
| uv                     | `uv sync`                        |
| pip                    | `pip install -r requirements.txt`|
| poetry                 | `poetry install`                 |

### 7. Configuración y Ejecución
- Copia el archivo de ejemplo de variables de entorno:
  ```bash
  cp .env.example .env
  ```
- Edita `.env` con tus credenciales (API de OpenAI, GCP, etc.).
- Ejecuta la aplicación:
  ```bash
  flask run
  ```

## Despliegue con Docker

Para un despliegue simplificado con Docker:

1. Asegúrate de estar en el directorio raíz del proyecto:
   ```bash
   cd zolkin-backend
   ```
2. Copia y configura el archivo `.env`:
   ```bash
   cp .env.example .env
   ```
3. Construye y levanta los contenedores:
   ```bash
   docker compose --project-name zolkin-backend up --build --detach
   ```

> [!IMPORTANT]
> Las URLs de los servicios (Redis y Milvus) pueden variar según el modo de despliegue.
> Revisa la configuración en `.env`.

### URLs en diferentes modos de despliegue
Cuando el despliegue es local, las URLs pueden ser:
- Redis: `redis://localhost:6379`
- Milvus: `http://localhost:19530`

Cuando el despliegue es con Docker, las URLs pueden ser:
- Redis: `redis://redis:6379`
- Milvus: `http://milvus:19530`

> [!NOTE]
> Las conexiones a estos dos contenedores en el código están definidas de manera que, al comentar sus URLs en el archivo .env, se conecten como si el despliegue se realizara en **local**.

> [!TIP]
> En sistemas Unix, se puede usar el Makefile para ejecutar comandos específicos.
> Ejecuta `make help` para ver las opciones disponibles.

## Ejemplos de Uso

Aquí tienes ejemplos de cómo interactuar con Zolkin mediante lenguaje natural:

| Prompt                                   | Resultado                                   |
| ---------------------------------------- | ------------------------------------------- |
| "Envía un correo a Ana sobre la reunión" | Envía un email a Ana desde Gmail.           |
| "Agenda una reunión mañana a las 10"     | Crea un evento en Google Calendar.          |
| "¿Qué correos recibí hoy?"               | Lista correos recibidos hoy                 |
| "¿Qué dice el PDF sobre el proyecto X?"  | Resumen generado del PDF usando RAG         |

## Componentes Principales

| Componente     | Función                                                       |
|----------------|---------------------------------------------------------------|
| Python         | Lenguaje principal del backend.                               |
| LangChain      | Integración de modelos de lenguaje, RAG y tools del agente    |
| Flask          | Framework web para la API del backend.                        |
| Docker         | Contenerización para despliegue simplificado.                 |
| Milvus         | Base de datos vectorial para el RAG.                          |
| LibreOffice    | Conversión de documentos a texto.                             |
| ImageMagick    | Procesamiento de imágenes para el RAG.                        |
| LangGraph      | Gestión de flujos de trabajo del LLM.                         |
| Redis          | Almacenamiento en memoria del historial de chat.              |
| OCRmyPDF       | OCR para extraer texto de PDFs escaneados.                    |
| PyMuPDF        | Procesamiento avanzado de PDFs.                               |
| GCP            | Integración con Gmail y Google Calendar.                      |
