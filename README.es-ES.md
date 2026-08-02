

<div align="center">
  <img src="assets/logo/fairmind-banner.png" alt="FairMind - Construye IA Ética y Confiable" width="800">
</div>

<br>

<div align="center">

**Plataforma de Gobernanza Ética de IA y Detección de Sesgos**
*Cumple con la Ley de IA de la UE, la Ley DPDP de India y el GDPR*

</div>

[![Estado del Backend](https://img.shields.io/badge/Backend-FastAPI-green)](https://api.fairmind.xyz)
[![Estado del Frontend](https://img.shields.io/badge/Frontend-Next.js-blue)](https://app-demo.fairmind.xyz)
[![Cobertura de Pruebas](https://img.shields.io/badge/Testing-80%25%2B-brightgreen)](./docs/TESTING_GUIDE.md)
[![Colaboradores](https://img.shields.io/github/contributors/adhit-r/fairmind)](https://github.com/adhit-r/fairmind/graphs/contributors)
[![Issues](https://img.shields.io/github/issues/adhit-r/fairmind/good%20first%20issue)](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)
[![Licencia](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![PRs Bienvenidos](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## Tabla de Contenidos

- [Panorama General](#overview)
- [Características Principales](#key-features)
- [Arquitectura](#architecture)
- [Inicio Rápido](#getting-started)
- [Documentación de la API](#api-documentation)
- [Características del Frontend](#frontend-features)
- [Stack Tecnológico](#technology-stack)
- [Estructura del Proyecto](#project-structure)
- [Desarrollo](#development)
- [Despliegue](#deployment)
- [Contribuciones](#contributing)
- [Seguridad](#security)
- [Licencia](#license)

---

## Panorama General

FairMind es una plataforma de Gobernanza de IA y Detección de Sesgos lista para producción, diseñada para sistemas de IA modernos. Proporciona herramientas integrales para detectar sesgos, generar informes de cumplimiento y garantizar el desarrollo ético de la IA en sistemas de Aprendizaje Automático Clásico, Modelos de Lenguaje Grande (LLMs) y sistemas Multimodales.

### Qué hace FairMind

FairMind ayuda a las organizaciones a:
- Detectar sesgos en modelos de IA en múltiples dominios (ML Clásico, LLMs, Multimodal)
- Generar automáticamente código de remediación para corregir los sesgos detectados
- Generar informes de cumplimiento para GDPR, Ley de IA de la UE y otras regulaciones
- Crear una Factura de Materiales de IA (AI BOM) para la transparencia del modelo
- Integrarse con herramientas de MLOps (Weights & Biases, MLflow) para el seguimiento de experimentos
- Monitorear el rendimiento y las métricas de sesgo en tiempo real
- Gestionar el ciclo de vida y la gobernanza de modelos

### Servicios en Vivo

- **API de Backend**: [api.fairmind.xyz](https://api.fairmind.xyz)
- **Documentación de la API**: [api.fairmind.xyz/docs](https://api.fairmind.xyz/docs)
- **Aplicación Frontend**: [app-demo.fairmind.xyz](https://app-demo.fairmind.xyz)

---

## ¿Qué Pueden Hacer los Usuarios?

<div align="center">
  <img src="assets/diagrams/user_features_workflow.png" alt="Características y Flujos de Trabajo para Usuarios de FairMind" width="900">
</div>

### Resumen del Estado de las Características

**🟢 Listo para Producción**: Detección de Sesgos • Evaluación de Modelos • Informes de Cumplimiento • Monitoreo en Tiempo Real • Integración con MLOps • Remediación Automatizada • Marketplace de Modelos • Informes Avanzados • Autenticación de Usuarios (Local)

**🟡 Backend Completo, UI Pendiente**: LLM-as-a-Judge

**⏳ Planificado Q2 2025**: Panel de Análisis Avanzado • Características Empresariales (RBAC, Equipos) • Internacionalización

**🔴 Fuera de Alcance**: Aplicaciones Móviles/Escritorio

---

## Características Principales

### 1. Detección Integral de Sesgos

**Detección de Sesgos en Aprendizaje Automático Clásico**
- Paridad Demográfica: Mide tasas iguales de predicción positiva entre grupos
- Probabilidades Igualadas: Asegura tasas iguales de verdaderos positivos y falsos positivos
- Análisis de Impacto Disperso: Cálculo de diferencia de paridad estadística
- Equidad Individual: Pruebas de equidad contrafactual
- Equidad de Grupo: Análisis de múltiples atributos protegidos

**Detección de Sesgos en Modelos de Lenguaje Grande (LLM)**
- WEAT (Prueba de Asociación de Incrustaciones de Palabras): Detecta sesgos implícitos en incrustaciones de palabras
- SEAT (Prueba de Asociación de Incrustaciones de Oraciones): Prueba sesgos en incrustaciones a nivel de oración
- Pruebas de Pares Mínimos: Detección sistemática de sesgos mediante comparaciones controladas
- Equidad Contrafactual: Prueba el comportamiento del modelo bajo escenarios contrafactuales
- Detección de Estereotipos: Identifica asociaciones estereotipadas en las salidas del modelo

**Detección de Sesgos Multimodales**
- Sesgo en Generación de Imágenes: Analiza sesgos en modelos de generación de imágenes (DALL-E, Stable Diffusion, etc.)
- Equidad en Generación de Audio: Prueba sesgos en modelos de síntesis de audio
- Sesgo en Contenido de Video: Detecta sesgos en generación y análisis de video
- Análisis de Estereotipos Transmodales: Identifica sesgos a través de diferentes modalidades
- Sesgo de Representación: Analiza la representación demográfica en contenido generado

### 2. Remediación Automatizada

FairMind genera código Python listo para producción para corregir los sesgos detectados:

<div align="center">
  <img src="assets/diagrams/remediation_flow.png" alt="Flujo de Remediación de FairMind" width="700">
</div>


- **Estrategias de Recalibración de Pesos**: Ajusta los pesos de las muestras para equilibrar grupos protegidos
- **Técnicas de Muestreo**: Sobre-muestreo/sub-muestreo para abordar el desequilibrio de clases
- **Optimización de Umbrales**: Encuentra umbrales de decisión óptimos para la equidad
- **Pipelines de Retreinamiento**: Flujos de trabajo completos de reinicio con restricciones de equidad
- **Métodos de Post-Procesamiento**: Técnicas de calibración y ajuste
- **Soluciones de Pre-Procesamiento**: Estrategias de transformación y limpieza de datos

### 3. Integración con MLOps

Integración perfecta con plataformas de seguimiento de experimentos:

<div align="center">
  <img src="assets/diagrams/mlops_integration.png" alt="Integración de MLOps de FairMind" width="700">
</div>


- **Integración con Weights & Biases**
  - Registro automático de resultados de pruebas de sesgo
  - Enlaces profundos desde los resultados de FairMind a los paneles de W&B
  - Seguimiento y comparación de experimentos
  - Control de versiones y registro de modelos

- **Integración con MLflow**
  - Seguimiento de experimentos y registro de modelos
  - Almacenamiento y gestión de artefactos
  - Seguimiento de servicio y despliegue de modelos
  - Registro de métricas de rendimiento

- **Configuración Sin Código**: Habilítelo mediante variables de entorno
- **Registro Automático**: Todas las pruebas de sesgo se registran automáticamente en las plataformas configuradas
- **Enlaces al Panel**: Enlaces directos desde los resultados a los paneles de experimentos

### 4. Cumplimiento y Gobernanza

**Factura de Materiales de IA (AI BOM)**
- Formato SBOM estándar para modelos de IA
- Seguimiento de componentes y procedencia
- Análisis de dependencias y escaneo de vulnerabilidades
- Linaje y historial de versiones del modelo
- Documentación de datos de entrenamiento

**Cumplimiento Regulatorio**

<div align="center">
  <img src="assets/diagrams/compliance_workflow.png" alt="Flujo de Cumplimiento de FairMind" width="700">
</div>

- **Evaluación de la Ley de IA de la UE**: Verificación automática de cumplimiento contra los requisitos de la Ley de IA de la UE
- **Cumplimiento del GDPR**: Informes de cumplimiento de protección de datos y privacidad
- **Ley DPDP (India)**: Cumplimiento de la Ley de Protección de Datos Personales Digitales
- **Marco de IA de India**: Cumplimiento de las Directrices de IA Responsable de NITI Aayog
- **ISO/IEC 42001**: Cumplimiento del Estándar de Sistema de Gestión de IA
- **NIST AI RMF**: Alineación con el Marco de Gestión de Riesgos
- **IEEE 7000**: Cumplimiento del proceso de consideraciones éticas

**Evaluación de Riesgos**
- Categorización automatizada de riesgos (Alto/Medio/Bajo)
- Evaluación de riesgos basada en políticas
- Análisis de brechas de cumplimiento
- Recomendaciones de remediación

**Recopilación de Evidencias**
- Generación integral de registros de auditoría
- Exportación de documentación de cumplimiento
- Mapeo regulatorio e informes
- Materiales de comunicación para partes interesadas

### 5. Registro y Gestión del Ciclo de Vida de Modelos

- Registro y control de versiones de modelos
- Gestión de metadatos
- Seguimiento de rendimiento
- Historial y tendencias de sesgos
- Comparación y evaluación de modelos
- Gestión de estados del ciclo de vida

### 6. Monitoreo en Tiempo Real

<div align="center">
  <img src="assets/diagrams/realtime_monitoring.png" alt="Monitoreo en Tiempo Real de FairMind" width="700">
</div>


- Monitoreo en vivo de métricas de sesgo
- Seguimiento de rendimiento
- Sistema de alertas para violaciones de umbrales
- Analíticas del panel
- Análisis de tendencias históricas

### 7. Marketplace de Modelos

- **Hub de Descubrimiento**: Plataforma centralizada para encontrar modelos justos y verificados
- **Tarjetas de Sesgo**: Métricas de equidad transparentes para cada modelo
- **Reseñas de la Comunidad**: Sistema de calificaciones y comentarios de usuarios
- **Seguimiento de Uso**: Monitorea la adopción y el rendimiento del modelo

### 8. Informes Avanzados

- **Generación de PDF**: Crea informes profesionales y listos para auditoría
- **Auditorías de Sesgo**: Desglose detallado de métricas de equidad y pasos de remediación
- **Certificados de Cumplimiento**: Prueba de adherencia a marcos regulatorios (Ley de IA de la UE, etc.)
- **Tarjetas de Modelo**: Documentación estandarizada para la transparencia del modelo

---

## Arquitectura

### Arquitectura del Sistema

<div align="center">
  <img src="assets/diagrams/fairmind_system_architecture.png" alt="Arquitectura del Sistema FairMind" width="800">
</div>

### Desglose de Componentes

**Servicios de Backend (+40 Módulos de Rutas API)**
- **Gobernanza Central**: Autenticación, Autorización, Gestión de Políticas
- **Motor de Detección de Sesgos**:
  - ML Clásico (Paridad Demográfica, Probabilidades Igualadas)
  - LLM Moderno (WEAT, SEAT, Pares Mínimos)
  - Multimodal (Imagen, Audio, Video)
- **Motor de Cumplimiento**:
  - **Stack de India**: Ley DPDP 2023, Marco NITI Aayog, Ley Digital India
  - **Global**: Ley de IA de la UE, GDPR, NIST AI RMF
  - **Sistema RAG**: Búsqueda semántica para documentos regulatorios
- **Monitor FairMind**:
  - Análisis de tokens en tiempo real
  - Seguimiento en vivo de métricas de sesgo
  - Alertas basadas en umbrales
- **Remediación Automatizada**: Generación de código para mitigación de sesgos
- **Integración con MLOps**: Conexión perfecta con W&B y MLflow

**Aplicación Frontend (+40 Páginas, +80 Componentes)**
- **Paneles**: Principal, Cumplimiento, Monitoreo en Tiempo Real
- **Herramientas Interactivas**: Pruebas de Sesgo, Generador de Remediación, Editor de Políticas
- **Visualizaciones**: Gráficos en tiempo real, Mapas de calor de métricas de sesgo, Tarjetas de puntuación de cumplimiento
- **Gestión de Evidencias**: Interfaz de usuario para recopilación y generación de informes automatizada

**Capa de Datos (Arquitectura Híbrida)**
- **SQLite (Local)**: Almacenamiento relacional principal para usuarios, autenticación y estado de la aplicación. Sin configuración, priorizado localmente.
- **DuckDB (Analíticas)**: Base de datos OLAP de alto rendimiento en proceso para análisis de conjuntos de datos y consultas pesadas de sesgos.
- **Supabase PostgreSQL (Opcional/Producción)**: Opción de base de datos escalable para producción.
- **Redis**: Caché de alto rendimiento para métricas en tiempo real.
- **Almacén Vectorial**: Incrustaciones para el sistema RAG regulatorio.
- **Almacenamiento de Archivos**: Sistema de archivos local o S3 para artefactos y conjuntos de datos.

---

## Inicio Rápido

### Requisitos Previos

- **Python 3.9+** (Backend)
- **Node.js 18+** (Frontend)
- **UV** (Gestor de paquetes Python) - [Guía de Instalación](https://github.com/astral-sh/uv)
- **Bun** (Entorno de ejecución JavaScript) - [Guía de Instalación](https://bun.sh/)

### Instalación Rápida

```bash
# Clonar el repositorio
git clone https://github.com/adhit-r/fairmind.git
cd fairmind

# Configuración del Backend
cd apps/backend
uv sync
cp config/env.example .env  # Configura tu entorno
# Crear cuenta de desarrollador (dev@fairmind.ai / dev)
uv run python scripts/create_dev_user.py
# Iniciar servidor
uv run python -m uvicorn api.main:app --reload --port 8000

# Configuración del Frontend (Nueva Terminal)
cd ../frontend
bun install
bun run dev
```

**Puntos de Acceso:**
- Frontend: http://localhost:1111
- API de Backend: http://localhost:8000
- Documentación de la API: http://localhost:8000/docs

### Configuración del Entorno

**Backend** (`apps/backend/.env`):
```env
# Base de datos (Por defecto SQLite local si no se establece)
# DATABASE_URL=sqlite:///./fairmind.db

# Caché (Opcional)
# REDIS_URL=redis://localhost:6379

# Integración con MLOps (Opcional)
WANDB_API_KEY=tu_clave_wandb
MLFLOW_TRACKING_URI=http://localhost:5000

# Seguridad
SECRET_KEY=tu-clave-secreta
JWT_SECRET=tu-secreto-jwt
JWT_ALGORITHM=HS256

# Entorno
ENVIRONMENT=desarrollo
```

**Frontend** (`apps/frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Configuración Detallada

Para instrucciones completas de configuración, consulta:
- [Guía de Configuración](SETUP.md) - Instalación y configuración completa
- [Guía de Inicio Rápido](QUICK_START.md) - Configuración en 5 minutos
- [Guía de Registro de Modelos](docs/MODEL_REGISTRATION_GUIDE.md) - Registrar y gestionar modelos
- [Guía de Cumplimiento en India](INDIA_COMPLIANCE_GUIDE.md) - Cumplimiento de la Ley DPDP y el Marco de IA de India

---

## Documentación de la API

### Documentación Interactiva

Documentación API interactiva completa con ejemplos de solicitud/respuesta:
- **Swagger UI**: [api.fairmind.xyz/docs](https://api.fairmind.xyz/docs)
- **ReDoc**: [api.fairmind.xyz/redoc](https://api.fairmind.xyz/redoc)

### Endpoints Principales de la API

**Detección de Sesgos**
- `POST /api/v1/bias/detect` - Detección de sesgos en ML Clásico
- `POST /api/v1/bias-v2/detect` - Detección de sesgos lista para producción
- `POST /api/v1/modern-bias/detect` - Detección de sesgos en LLM (WEAT, SEAT)
- `POST /api/v1/multimodal-bias/image-detection` - Sesgo en generación de imágenes
- `POST /api/v1/multimodal-bias/audio-detection` - Sesgo en generación de audio
- `POST /api/v1/multimodal-bias/video-detection` - Sesgo en contenido de video

**Remediación**
- `POST /api/v1/bias/remediate` - Generar código de remediación
- `GET /api/v1/bias/remediation-strategies` - Listar estrategias disponibles

**Integración con MLOps**
- `GET /api/v1/mlops/status` - Verificar estado de integración
- `POST /api/v1/mlops/log-test` - Registrar experimentos manualmente
- `GET /api/v1/mlops/experiments` - Listar experimentos registrados

**Cumplimiento y Gobernanza**
- `POST /api/v1/compliance/report` - Generar informe de cumplimiento
- `POST /api/v1/aibom/generate` - Crear Factura de Materiales de IA
- `GET /api/v1/compliance/frameworks` - Listar marcos compatibles

**Gestión de Modelos**
- `GET /api/v1/core/models` - Listar modelos registrados
- `POST /api/v1/core/models` - Registrar nuevo modelo
- `GET /api/v1/core/models/{id}` - Obtener detalles del modelo
- `PUT /api/v1/core/models/{id}` - Actualizar modelo
- `DELETE /api/v1/core/models/{id}` - Eliminar modelo

**Monitoreo y Analíticas**
- `GET /api/v1/database/dashboard-stats` - Estadísticas del panel
- `GET /api/v1/monitoring/metrics` - Métricas en tiempo real
- `GET /api/v1/analytics/trends` - Tendencias históricas

**Sistema**
- `GET /health` - Endpoint de verificación de estado
- `GET /api/v1/system/info` - Información del sistema

**Total de Endpoints API**: 50+

Para la referencia completa de la API, consulta [Documentación de la API](docs/API_ENDPOINTS.md)

---

## Características del Frontend

### Páginas del Panel

| Página | Ruta | Descripción |
|------|-------|-------------|
| **Panel Principal** | `/dashboard` | Vista general del sistema, métricas de estado, actividad reciente |
| **Detección de Sesgos** | `/bias` | Subir conjuntos de datos, configurar pruebas, ver métricas de sesgo en ML Clásico |
| **Sesgo Moderno** | `/modern-bias` | Interfaz de detección de sesgos en LLM (WEAT, SEAT, Pares Mínimos) |
| **Sesgo Multimodal** | `/multimodal-bias` | Análisis de sesgo en imágenes, audio y video |
| **Resultados de Pruebas** | `/tests/[id]` | Análisis detallado de pruebas, enlaces a W&B/MLflow, exportación JSON |
| **Remediación** | `/remediation` | Seleccionar estrategias, generar código Python |
| **Panel de Cumplimiento** | `/compliance-dashboard` | Gestión de políticas, generación de informes |
| **AI BOM** | `/ai-bom` | Generación y seguimiento de la Factura de Materiales |
| **Modelos** | `/models` | Registro de modelos, control de versiones, gestión del ciclo de vida |
| **Monitoreo** | `/monitoring` | Métricas en tiempo real, alertas, seguimiento de rendimiento |
| **Analíticas** | `/analytics` | Analíticas de rendimiento, análisis de tendencias, insights |
| **Configuración** | `/settings` | Configuración de MLOps, gestión de perfil, preferencias |

### Características Clave del Frontend

- **Sistema de Diseño Neobrutal**: Diseño de UI moderno y audaz
- **Diseños Responsivos**: Funciona en escritorio, tableta y móvil
- **Actualizaciones en Tiempo Real**: Métricas y actualizaciones de estado en vivo
- **Visualizaciones Interactivas**: Gráficos y diagramas para métricas de sesgo
- **Capacidades de Exportación**: Opciones de exportación JSON, CSV, PDF
- **Enlaces Profundos**: Enlaces directos a paneles de MLOps
- **Soporte para Modo Oscuro**: Personalización de temas
- **Accesibilidad**: Cumplimiento WCAG (en progreso)

---

## Stack Tecnológico

### Backend

**Framework Central**
- Python 3.9+
- FastAPI 0.121.1
- Uvicorn (servidor ASGI)
- Pydantic (validación de datos)

**Aprendizaje Automático**
- scikit-learn 1.7.2
- pandas 2.3.3
- numpy 2.3.4
- scipy 1.16.3
- transformers (HuggingFace)

**Base de Datos y Almacenamiento**
- SQLAlchemy 2.0.44 (ORM)
- Supabase (PostgreSQL para producción)
- SQLite (desarrollo local)
- Redis 7.0.1 (caché)

**Autenticación y Seguridad**
- JWT (JSON Web Tokens)
- bcrypt (hash de contraseñas)
- Middleware de encabezados de seguridad
- Limitación de tasa

**Integraciones**
- SDK de Supabase
- API de Weights & Biases
- Seguimiento de MLflow
- AWS S3 (boto3)

**Pruebas**
- pytest con cobertura
- Playwright (E2E)
- Cobertura de pruebas: objetivo >80%

### Frontend

**Framework Central**
- Next.js 14.2.32
- React 18.3.1
- TypeScript 5.5.3

**Bibliotecas de UI**
- Radix UI (+15 componentes)
- Shadcn UI
- Sistema de diseño Neobrutalism
- Tailwind CSS 3.4.4

**Estado y Datos**
- Ganchos de React
- React Hook Form 7.51.0
- Zod 3.23.8 (validación)

**Visualización**
- Recharts 2.12.0
- Tabler Icons
- Lucide React

**Pruebas**
- Playwright 1.44.0
- Suite de pruebas E2E (11 archivos)

**Herramientas de Construcción**
- Bun (gestor de paquetes)
- PostCSS
- Autoprefixer

### DevOps e Infraestructura

**Despliegue**
- Netlify (alojamiento frontend)
- Soporte para Docker
- Configuraciones de Kubernetes

**CI/CD**
- GitHub Actions
- Pruebas automatizadas
- Protección de ramas habilitada
- Escaneo de seguridad (CodeQL, Dependabot)

**Monitoreo**
- Endpoints de verificación de estado
- Registro estructurado
- Seguimiento de errores (Sentry)

---

## Estructura del Proyecto

```
fairmind/
├── apps/
│   ├── backend/              # Backend FastAPI
│   │   ├── api/              # Rutas API (27 módulos)
│   │   │   ├── routes/        # Manejadores de rutas
│   │   │   └── main.py       # Aplicación FastAPI
│   │   ├── services/         # Lógica de negocio (17 módulos)
│   │   ├── config/           # Configuración
│   │   ├── middleware/       # Seguridad y manejo de solicitudes
│   │   ├── database/         # Modelos y migraciones de base de datos
│   │   ├── tests/            # Suite de pruebas (21 archivos)
│   │   └── pyproject.toml    # Dependencias Python
│   │
│   ├── frontend/             # Frontend Next.js
│   │   ├── src/
│   │   │   ├── app/          # Enrutador de app Next.js (+30 páginas)
│   │   │   ├── components/   # Componentes React (+60)
│   │   │   └── lib/          # Utilidades y clientes API
│   │   ├── tests/            # Pruebas E2E (Playwright)
│   │   └── package.json      # Dependencias Node
│   │
│   ├── website/              # Sitio de marketing (Astro)
│   └── ml/                    # Utilidades y experimentos de ML
│
├── docs/                      # Documentación
│   ├── development/           # Guías de desarrollo
│   ├── deployment/            # Guías de despliegue
│   ├── architecture/          # Documentación de arquitectura
│   └── API_ENDPOINTS.md       # Referencia API
│
├── scripts/                   # Scripts de utilidad
├── k8s/                       # Configuraciones de Kubernetes
└── archive/                    # Archivos y documentación archivados
```

---

## Desarrollo

### Ejecución Local

**Desarrollo del Backend**
```bash
cd apps/backend
uv sync
uv run python -m uvicorn api.main:app --reload --port 8000
```

**Desarrollo del Frontend**
```bash
cd apps/frontend
bun install
bun run dev
```

### Ejecución de Pruebas

**Pruebas del Backend**
```bash
cd apps/backend
uv run pytest
uv run pytest --cov=api --cov-report=html
```

**Pruebas E2E del Frontend**
```bash
cd apps/frontend
bun run test
bun run test:ui
```

**Pruebas E2E del Backend**
```bash
cd apps/backend
uv run pytest tests/e2e/ -m e2e
```

### Calidad del Código

- **Linting**: Black, isort, flake8 (Python), ESLint (TypeScript)
- **Verificación de Tipos**: mypy (Python), compilador de TypeScript
- **Formato**: Black (Python), Prettier (TypeScript)
- **Ganchos Pre-commit**: Verificaciones automáticas de calidad de código

### Directrices de Desarrollo

Consulta la [Guía de Contribuciones](docs/CONTRIBUTING.md) para:
- Directrices de estilo de código
- Convenciones de mensajes de commit
- Proceso de solicitudes de extracción (Pull Request)
- Requisitos de pruebas

---

## Despliegue

### Despliegue en Producción

**Backend**
- Instrucciones de despliegue pendientes


**Frontend (Netlify)**
- Despliegues automáticos desde la rama principal
- Comando de construcción: `bun run build`
- Variables de entorno en el panel de Netlify
- Distribución por CDN

### Despliegue con Docker

```bash
# Construir imagen del backend
cd apps/backend
docker build -t fairmind-backend .

# Ejecutar backend
docker run -p 8000:8000 fairmind-backend

# Construir imagen del frontend
cd apps/frontend
docker build -t fairmind-frontend .

# Ejecutar frontend
docker run -p 3000:3000 fairmind-frontend
```

### Despliegue en Kubernetes

Configuraciones de Kubernetes disponibles en el directorio `k8s/`:
- Despliegue del backend
- Despliegue del frontend
- ConfigMaps y Secrets
- Configuración de Ingress

Consulta la [Guía de Despliegue](docs/deployment/DEPLOYMENT_GUIDE_2025.md) para instrucciones detalladas.

---

## Contribuciones

FairMind es un proyecto de código abierto y agradece las contribuciones de la comunidad.

### Cómo Contribuir

1. **Haz un fork del repositorio**
2. **Crea una rama para la característica** (`git checkout -b feature/nueva-funcionalidad`)
3. **Realiza tus cambios** siguiendo nuestros estándares de codificación
4. **Escribe o actualiza las pruebas** según sea necesario
5. **Confirma tus cambios** utilizando el formato de commit convencional
6. **Empuja a tu rama** (`git push origin feature/nueva-funcionalidad`)
7. **Abre una Pull Request** apuntando a la rama `main`

### Directrices de Contribución

- Sigue las directrices de estilo de código en [CONTRIBUTING.md](docs/CONTRIBUTING.md)
- Escribe pruebas para nuevas características
- Actualiza la documentación según sea necesario
- Utiliza mensajes de commit convencionales
- Asegúrate de que todas las pruebas pasen antes de enviar

### Primeras Contribuciones (Good First Issues)

Tenemos más de 21 issues ideales para nuevos colaboradores:
- [Ver Good First Issues](https://github.com/adhit-r/fairmind/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)

### Proceso de Revisión de Código

- Todos los PR requieren al menos 1 revisión antes de fusionar
- La rama principal está protegida
- Las pruebas automatizadas deben pasar
- Se aplican verificaciones de calidad de código

---

## Seguridad

FairMind toma la seguridad en serio. Seguimos prácticas de divulgación responsable.

### Reporte de Vulnerabilidades

- **Correo electrónico**: security@fairmind.xyz
- **Tiempo de respuesta**: 24 horas
- **Por favor, no reportes vulnerabilidades de seguridad a través de issues públicos de GitHub**

### Herramientas de Seguridad

- CodeQL para detección de vulnerabilidades
- Dependabot para escaneo de dependencias
- Auditorías de seguridad regulares
- Verificaciones de seguridad automatizadas en CI/CD

### Características de Seguridad

- Autenticación basada en JWT
- Hash de contraseñas con bcrypt
- Middleware de encabezados de seguridad
- Limitación de tasa
- Validación y sanitización de entradas
- Prevención de inyección SQL
- Protección XSS

Consulta la [Política de Seguridad](docs/SECURITY.md) para la política completa.

---

## Estado del Proyecto

### Fase Actual: Q1 2025 (Fundación)

**Completado**
- Características centrales de gobernanza de IA
- Detección moderna de sesgos en LLM (WEAT, SEAT, Pares Mínimos)
- Análisis de sesgos multimodales (Imagen, Audio, Video)
- Integración con MLOps (W&B, MLflow)
- Informes de cumplimiento (Ley de IA de la UE, GDPR)
- Generación de AI BOM
- Despliegue en producción
- Pruebas integrales (+80% de cobertura)
- Suite de documentación

**En Progreso**
- Automatización de pipelines CI/CD
- Optimizaciones de rendimiento del frontend
- Remediación de vulnerabilidades de seguridad
- Mejoras de accesibilidad

**Planificado**
- Responsividad móvil
- Internacionalización (i18n)
- Panel de analíticas avanzadas
- Características empresariales

Consulta [ROADMAP.md](ROADMAP.md) para el mapa de ruta detallado.

---

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - consulta el archivo [LICENSE](LICENSE) para más detalles.

---

## Soporte y Comunidad

**Recursos**
- [Documentación](docs/)
- [Issues de GitHub](https://github.com/adhit-r/fairmind/issues)
- [Discusiones de GitHub](https://github.com/adhit-r/fairmind/discussions)
- [Guía de Contribuciones](docs/CONTRIBUTING.md)

**Contacto**
- Repositorio: [github.com/adhit-r/fairmind](https://github.com/adhit-r/fairmind)
- correo de soporte : adhi.r@fairmind.xyz 
---

**FairMind - Haciendo la IA justa, transparente y responsable para todos.**

*Construido para la comunidad de ética en IA*
