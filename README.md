# Plataforma de Hosting ROBLE

Plataforma de hosting de páginas web basada en contenedores Docker con autenticación institucional mediante Roble. Permite a usuarios desplegar sitios web desde repositorios de GitHub con subdominios automáticos y gestión eficiente de recursos.

## Video de Demostración

**[Ver Video en YouTube](PENDIENTE_AGREGAR_ENLACE)**

Contenido del video:
- Registro e inicio de sesión con Roble
- Creación y despliegue de un proyecto desde GitHub
- Acceso mediante subdomain local
- Funcionamiento del rate limiting
- Auto-apagado tras 30 minutos de inactividad
- Auto-reinicio automático al recibir peticiones

## Características Principales

- Autenticación mediante sistema Roble
- Deploy automático desde repositorios GitHub
- Subdominios dinámicos: `http://proyecto.usuario.localhost`
- Límites de recursos por contenedor (CPU: 0.5 cores, RAM: 256MB)
- Rate limiting: 100 peticiones/minuto por IP
- Auto-apagado tras 30 minutos de inactividad
- Auto-reinicio al recibir nuevas peticiones
- Dashboard web para gestión de proyectos
- Reverse proxy con Nginx

## Templates Dockerizados Disponibles

Los siguientes templates incluyen Dockerfile y docker-compose.yml listos para usar:

1. **Template Estático** - HTML + CSS + JavaScript
   - Repositorio: https://github.com/Charlsz/host_roble/tree/main/templates/static_template
   - Archivos: `index.html`, `Dockerfile`, `docker-compose.yml`
   - Servidor: Nginx (puerto 80)

2. **Template React** - React con CDN (sin build)
   - Repositorio: https://github.com/Charlsz/host_roble/tree/main/templates/react_template
   - Archivos: `index.html`, `Dockerfile`, `docker-compose.yml`
   - Servidor: Nginx (puerto 80)

3. **Template Flask** - Python + Flask + Gunicorn
   - Repositorio: https://github.com/Charlsz/host_roble/tree/main/templates/flask_template
   - Archivos: `app.py`, `requirements.txt`, `Dockerfile`, `docker-compose.yml`
   - Servidor: Gunicorn (puerto 5000)

Instrucciones de uso: [templates/README.md](./templates/README.md)

## Documentación Técnica

Para información detallada sobre arquitectura, componentes, flujo de trabajo, estrategias de seguridad y optimización de recursos, consultar:

**[Documento Técnico Completo](./DOCUMENTACION_TECNICA.md)**

El documento incluye:
- Descripción de la arquitectura y componentes del sistema
- Diagramas de flujo de trabajo (autenticación, deploy, monitoreo)
- Estrategia de seguridad (rate limiting, aislamiento de contenedores, validación)
- Optimización de recursos (límites por contenedor, auto-apagado, gestión de puertos)

## Instalación y Uso

### Prerequisitos

- Docker Desktop
- Git
- Cuenta en Roble (sistema de autenticación institucional)

### Iniciar la plataforma

```bash
# Clonar el repositorio
git clone https://github.com/Charlsz/host_roble.git
cd host_roble

# Iniciar todos los servicios
docker-compose up -d

# Verificar que todo está corriendo
docker-compose ps
```

### Acceder a la plataforma

1. Abrir dashboard: http://localhost:8080
2. Iniciar sesión con credenciales de Roble
3. Crear nuevo proyecto:
   - Nombre del proyecto
   - URL del repositorio GitHub
   - Branch (opcional, default: main)

## Flujo de Trabajo para Usuarios

### 1. Seleccionar y clonar un template

Navegar a la carpeta templates/ y copiar el template deseado a un nuevo repositorio:

```bash
# Crear directorio para tu proyecto
mkdir mi-proyecto
cd mi-proyecto

# Copiar archivos del template
cp -r ../host_roble/templates/static_template/* .

# Inicializar repositorio
git init
git add .
git commit -m "Initial commit con template"
git remote add origin https://github.com/tu-usuario/mi-proyecto.git
git push -u origin main
```

### 2. Personalizar el proyecto

Editar los archivos según necesidades y hacer push de los cambios.

### 3. Desplegar en la plataforma

- Dashboard → "Nuevo Proyecto"
- Ingresar URL del repositorio
- Click "Crear y Desplegar"
- Esperar 30-90 segundos (build y deploy)

### 4. Acceder al proyecto

El proyecto estará disponible en:
- http://nombreProyecto.tuUsuario.localhost
- http://localhost:PUERTO_ASIGNADO (entre 7000-7999)

## Arquitectura del Sistema

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Dashboard  │─────→│   Manager   │─────→│    Roble    │
│ (puerto 8080│      │ (puerto 5000│      │  (Auth API) │
└─────────────┘      └─────────────┘      └─────────────┘
                            │
                            ↓
                     ┌─────────────┐
                     │Docker Engine│
                     │             │
                     │ ┌─────────┐ │
                     │ │Project 1│ │
                     │ │(7000)   │ │
                     │ └─────────┘ │
                     │ ┌─────────┐ │
                     │ │Project 2│ │
                     │ │(7001)   │ │
                     │ └─────────┘ │
                     └─────────────┘
                            ↑
                            │
                     ┌─────────────┐
                     │Nginx Proxy  │
                     │(puerto 80)  │
                     │Subdomain    │
                     │routing      │
                     └─────────────┘
```

### Componentes principales

- **Dashboard**: Interfaz web (HTML/CSS/JavaScript)
- **Manager**: API REST en Flask para gestión de proyectos
- **Deploy Service**: Orquestador de clonación, build y deploy
- **Activity Monitor**: Servicio de monitoreo de inactividad (thread en background)
- **Nginx Proxy**: Reverse proxy con configuración dinámica y rate limiting
- **Roble Client**: Integración con sistema de autenticación

## Gestión de Recursos

### Límites por contenedor

Cada proyecto desplegado tiene límites estrictos:

- **CPU**: 0.5 cores (50% de 1 CPU)
- **RAM**: 256 MB máximo
- **Puerto**: Asignación dinámica del pool 7000-7999

### Rate Limiting

Protección contra sobrecarga implementada en Nginx:

- **Límite**: 100 peticiones por minuto por IP
- **Burst**: 20 peticiones adicionales temporales
- **Respuesta**: HTTP 429 (Too Many Requests) al exceder

### Auto-apagado por inactividad

Política de optimización de recursos:

- Contenedores sin actividad durante 30 minutos se detienen automáticamente
- Los contenedores detenidos NO se eliminan (imagen y datos persisten)
- Al recibir nueva petición, el contenedor se reinicia automáticamente en 3-5 segundos
- El dashboard muestra tiempo de inactividad en tiempo real

## API del Manager

Endpoints principales (puerto 5000):

```
POST   /api/auth/login              - Autenticación con Roble
POST   /api/auth/register           - Registro de usuario
GET    /api/projects                - Listar proyectos del usuario
POST   /api/projects                - Crear y desplegar proyecto
DELETE /api/projects/<id>           - Eliminar proyecto
POST   /api/projects/<id>/rebuild   - Reconstruir proyecto
POST   /api/projects/activity/<name> - Registrar actividad
```

## Estructura del Proyecto

```
host_roble/
├── manager/                 - API Flask principal
│   ├── manager.py          - Entry point
│   ├── auth_routes.py      - Rutas de autenticación
│   ├── projects_routes.py  - CRUD de proyectos
│   ├── deploy_service.py   - Servicio de deploy
│   ├── activity_monitor.py - Monitor de inactividad
│   └── roble_client.py     - Cliente API Roble
├── dashboard/              - Frontend web
│   ├── src/
│   │   ├── index.html
│   │   ├── templates.html
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── Dockerfile
├── nginx/                  - Reverse proxy
│   ├── nginx.conf
│   └── conf.d/            - Configs dinámicas
├── templates/             - Templates base
│   ├── static_template/
│   ├── react_template/
│   ├── flask_template/
│   └── README.md
├── microservices/        - Microservicios auxiliares
├── docker-compose.yml    - Orquestación
└── DOCUMENTACION_TECNICA.md
```

## Testing

### Verificar servicios

```bash
# Ver estado de servicios
docker-compose ps

# Ver logs del manager
docker-compose logs -f manager

# Ver logs de nginx
docker-compose logs -f nginx_proxy
```

### Probar template localmente

```bash
cd templates/static_template
docker build -t test-static .
docker run -p 8001:80 test-static
# Abrir http://localhost:8001
```

## Comandos Útiles

```bash
# Detener todos los servicios
docker-compose down

# Reconstruir desde cero
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f

# Limpiar sistema Docker
docker system prune -a -f

# Verificar red Docker
docker network inspect host_roble_microservices_network

# Ver puertos en uso
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

## Troubleshooting

### Subdomain no funciona

Verificar que el contenedor esté en la red correcta:

```bash
docker inspect <nombre_contenedor> | grep NetworkMode
```

### Puerto ocupado

Ver puertos en uso:

```bash
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

### Build falla

Ver logs detallados:

```bash
docker-compose logs manager
```

## Equipo

**Integrantes del Proyecto:**

- [Carlos Galvis] - [Developer]
<!-- - [Nombre Integrante 2] - [Rol/Responsabilidad]
- [Nombre Integrante 3] - [Rol/Responsabilidad] -->

**Curso**: Estructura del Computador II  
**Universidad del Norte**  
**Año**: 2025

## Licencia y Autorización

Al presentar este proyecto, los integrantes del equipo autorizan expresamente que la solución (total o parcial) pueda ser utilizada por Roble como base para ofrecer servicios de hosting académicos o institucionales en el futuro, con reconocimiento público de autoría.

## Repositorio

GitHub: https://github.com/Charlsz/host_roble
