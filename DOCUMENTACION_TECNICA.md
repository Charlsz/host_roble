# Documentación Técnica - Plataforma de Hosting ROBLE

**Proyecto**: Plataforma de Hosting Basada en Contenedores  
**Curso**: Estructura del Computador II  
**Universidad del Norte**  
**Año**: 2025

---

## 📋 Tabla de Contenidos

1. [Descripción de la Arquitectura](#arquitectura)
2. [Componentes del Sistema](#componentes)
3. [Flujo de Trabajo](#flujo-de-trabajo)
4. [Estrategia de Seguridad](#seguridad)
5. [Optimización de Recursos](#optimización)
6. [Tecnologías Utilizadas](#tecnologías)

---

## 🏗️ Arquitectura del Sistema {#arquitectura}

### Diagrama de Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                     USUARIO (Navegador)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │   Dashboard (Puerto 8080)     │
         │   - Frontend HTML/CSS/JS      │
         │   - Interfaz de usuario       │
         └───────────────┬───────────────┘
                         │ HTTP/API
                         ▼
         ┌───────────────────────────────┐
         │   Manager API (Puerto 5000)   │
         │   - Flask REST API            │
         │   - Deploy Service            │
         │   - Activity Monitor          │
         │   - Roble Client             │
         └───────┬───────────────┬───────┘
                 │               │
        Autenticación         Deploy
                 │               │
                 ▼               ▼
         ┌───────────┐   ┌─────────────────┐
         │   Roble   │   │  Docker Engine  │
         │   (Auth)  │   │                 │
         └───────────┘   │  ┌───────────┐  │
                         │  │ Project 1 │  │
                         │  │(Port 7000)│  │
                         │  └───────────┘  │
                         │  ┌───────────┐  │
                         │  │ Project 2 │  │
                         │  │(Port 7001)│  │
                         │  └───────────┘  │
                         └────────┬────────┘
                                  │
                         ┌────────┴────────┐
                         │  Nginx Proxy    │
                         │  (Puerto 80)    │
                         │  - Subdomain    │
                         │    routing      │
                         │  - Rate limit   │
                         └─────────────────┘
                                  │
                         Subdominios locales:
                    proyecto.usuario.localhost
```

### Arquitectura de Red Docker

```
┌─────────────────────────────────────────────────────┐
│  host_roble_microservices_network (Bridge)         │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │ Manager  │  │Dashboard │  │  Nginx   │         │
│  │ :5000    │  │  :8080   │  │  :80     │         │
│  └──────────┘  └──────────┘  └──────────┘         │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │Project 1 │  │Project 2 │  │Project N │         │
│  │ :7000    │  │ :7001    │  │ :700X    │         │
│  └──────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────────────────────────────┘
```

---

## 🧩 Componentes del Sistema {#componentes}

### 1. **Dashboard (Frontend)**

**Tecnología**: HTML5, CSS3, Vanilla JavaScript  
**Puerto**: 8080  
**Función**: Interfaz web para usuarios

**Características**:
- Formulario de login/registro
- Visualización de proyectos activos/detenidos
- Creación de nuevos proyectos
- Monitoreo de inactividad en tiempo real
- Página de templates con código copiable
- Auto-refresh cada 5 segundos

**Archivos principales**:
- `dashboard/src/index.html` - Página principal
- `dashboard/src/templates.html` - Catálogo de templates
- `dashboard/src/js/app.js` - Lógica del frontend
- `dashboard/src/css/style.css` - Estilos

---

### 2. **Manager (Backend API)**

**Tecnología**: Python 3.11 + Flask  
**Puerto**: 5000  
**Función**: API REST central, orquestador del sistema

**Módulos**:

#### 2.1 `manager.py` (Entry Point)
- Inicialización de Flask app
- Registro de blueprints
- Inicialización de ActivityMonitor
- Configuración CORS

#### 2.2 `auth_routes.py` (Autenticación)
- `POST /api/auth/login` - Login con Roble
- `POST /api/auth/register` - Registro de usuarios
- Integración con Roble API

#### 2.3 `projects_routes.py` (CRUD Proyectos)
- `GET /api/projects` - Listar proyectos del usuario
- `POST /api/projects` - Crear y desplegar proyecto
- `DELETE /api/projects/<id>` - Eliminar proyecto
- `POST /api/projects/<id>/rebuild` - Reconstruir contenedor
- `POST /api/projects/activity/<name>` - Registrar actividad

#### 2.4 `deploy_service.py` (Orquestador de Deploy)

**Responsabilidades**:
1. **Clonación de repositorios**:
   ```python
   git clone --depth 1 <repo_url> <temp_dir>
   ```

2. **Build de imágenes Docker**:
   ```python
   docker.images.build(path=temp_dir, tag=image_name)
   ```

3. **Deploy de contenedores**:
   ```python
   docker.containers.run(
       image=image_name,
       name=container_name,
       ports={internal_port: host_port},
       network='host_roble_microservices_network',
       mem_limit='256m',
       cpu_period=100000,
       cpu_quota=50000  # 0.5 CPU
   )
   ```

4. **Generación de configuración Nginx**:
   - Crea archivos `.conf` en `/nginx_configs`
   - Configura subdomain routing
   - Aplica rate limiting
   - Recarga Nginx

5. **Gestión de puertos**:
   - Rango: 7000-7999
   - Asignación automática
   - Liberación al eliminar proyecto

#### 2.5 `activity_monitor.py` (Monitor de Inactividad)

**Función**: Thread en background que monitorea actividad de contenedores

**Parámetros**:
- `CHECK_INTERVAL = 60` segundos (verificación cada minuto)
- `INACTIVITY_TIMEOUT = 1800` segundos (30 minutos)

**Flujo**:
1. Inicializa timestamp `last_activity` para cada contenedor
2. Loop cada 60 segundos verifica tiempo de inactividad
3. Si `now - last_activity > 30 min` → detiene contenedor
4. Al recibir petición nueva → reinicia contenedor automáticamente

**Endpoints**:
- `update_activity(container_name)` - Actualiza timestamp
- `restart_container_if_stopped(container_name)` - Reinicia si está detenido

#### 2.6 `roble_client.py` (Cliente Roble)
- Integración con API de Roble
- CRUD de usuarios en Roble
- Validación de tokens

---

### 3. **Nginx Reverse Proxy**

**Tecnología**: Nginx Alpine  
**Puerto**: 80  
**Función**: Reverse proxy con subdomain routing y rate limiting

**Configuración Principal** (`nginx/nginx.conf`):

```nginx
# Rate Limiting Zone
limit_req_zone $binary_remote_addr zone=general:10m rate=100r/m;

http {
    # Configuración general
    include /etc/nginx/conf.d/*.conf;
}
```

**Configuración por Proyecto** (generada dinámicamente):

```nginx
# Ejemplo: test.usuario.conf
upstream test_usuario_backend {
    server project_usuario_test:80;
}

server {
    listen 80;
    server_name test.usuario.localhost;
    
    location / {
        limit_req zone=general burst=20 nodelay;
        proxy_pass http://test_usuario_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Características**:
- Resolución DNS de contenedores por nombre
- Rate limiting: 100 req/min con burst de 20
- Configuración dinámica (archivos generados por Manager)
- Recarga sin downtime

---

### 4. **Activity Monitor Service**

**Ubicación**: Thread dentro de Manager  
**Propósito**: Optimizar recursos apagando contenedores inactivos

**Algoritmo**:

```python
def _monitor_loop():
    while True:
        for container in get_all_project_containers():
            inactive_time = now - last_activity[container.name]
            
            if inactive_time > 30 * 60:  # 30 minutos
                if container.status == 'running':
                    container.stop()
                    log(f"Contenedor {container.name} detenido por inactividad")
        
        sleep(60)  # Check cada minuto
```

**Integración con Dashboard**:
- Dashboard muestra "Inactivo: X min" en tiempo real
- Alerta visual cuando > 20 minutos
- Tracking de actividad mediante endpoint API

---

## 🔄 Flujo de Trabajo del Sistema {#flujo-de-trabajo}

### 1. Flujo de Registro e Inicio de Sesión

```
Usuario → Dashboard → Manager → Roble API
  │         │           │          │
  │  Form   │  POST     │  POST    │
  │ Submit  │  /login   │  /auth   │
  └────────→└──────────→└─────────→│
                                   │
  ┌────────────────────────────────┘
  │ Token JWT
  ▼
Dashboard guarda token
Usuario autenticado
```

### 2. Flujo de Deploy de Proyecto

```
1. Usuario selecciona template
   └─→ Copia archivos a su repo GitHub

2. Usuario completa formulario en Dashboard
   - Nombre: "mi-proyecto"
   - Repo: "https://github.com/user/mi-proyecto"

3. Dashboard → POST /api/projects
   └─→ Manager recibe solicitud

4. Manager → deploy_service.py
   ├─→ 4.1 Clonar repo (git clone --depth 1)
   ├─→ 4.2 Build imagen Docker
   │        └─→ Nombre: project_user_mi-proyecto:latest
   ├─→ 4.3 Asignar puerto (ej: 7000)
   ├─→ 4.4 Crear contenedor
   │        ├─→ Network: host_roble_microservices_network
   │        ├─→ Limits: 256MB RAM, 0.5 CPU
   │        └─→ Port mapping: 7000:80
   ├─→ 4.5 Generar nginx config
   │        └─→ /nginx_configs/mi-proyecto.user.conf
   └─→ 4.6 Reload nginx

5. Proyecto accesible en:
   ├─→ http://mi-proyecto.user.localhost
   └─→ http://localhost:7000
```

### 3. Flujo de Monitoreo de Inactividad

```
ActivityMonitor (Loop cada 60s)
  │
  ├─→ Verifica cada contenedor
  │    └─→ Calcula: tiempo_inactivo = now - last_activity
  │
  ├─→ Si tiempo_inactivo > 30 min:
  │    └─→ container.stop()
  │         └─→ Contenedor detenido (no eliminado)
  │
  └─→ Al recibir petición nueva:
       └─→ Nginx → 502 Bad Gateway (contenedor detenido)
            └─→ Dashboard detecta → llama activity endpoint
                 └─→ Manager verifica estado
                      └─→ container.start()
                           └─→ Contenedor reiniciado
```

### 4. Flujo de Rate Limiting

```
Usuario hace petición
  │
  └─→ Nginx recibe request
       │
       ├─→ Nginx verifica limit_req_zone
       │    └─→ Cuenta peticiones de IP en ventana de 1 min
       │
       ├─→ Si peticiones < 100:
       │    └─→ proxy_pass → contenedor proyecto
       │         └─→ Respuesta 200 OK
       │
       └─→ Si peticiones > 100 (+ burst 20):
            └─→ Respuesta 429 Too Many Requests
```

---

## 🔒 Estrategia de Seguridad {#seguridad}

### 1. **Autenticación y Autorización**

- **Integración con Roble**: Sistema de autenticación institucional
- **Tokens JWT**: Sesiones seguras sin estado
- **Validación por usuario**: Cada usuario solo ve/modifica sus proyectos
- **CORS**: Configurado para permitir solo orígenes autorizados

### 2. **Rate Limiting (Protección DDoS)**

**Implementación en Nginx**:
```nginx
limit_req_zone $binary_remote_addr zone=general:10m rate=100r/m;
limit_req zone=general burst=20 nodelay;
```

**Beneficios**:
- Protege contra ataques de denegación de servicio
- Límite: 100 peticiones/minuto por IP
- Burst temporal de 20 peticiones adicionales
- Respuesta HTTP 429 cuando se excede

### 3. **Aislamiento de Contenedores**

- **Network isolation**: Red Docker personalizada
- **Resource limits**: CPU y RAM limitados por contenedor
- **User namespaces**: Contenedores no ejecutan como root
- **Read-only filesystem**: Código inmutable en tiempo de ejecución

### 4. **Validaciones de Entrada**

**En el Dashboard**:
- Nombres de proyecto: solo `[a-z0-9\-]+`
- URLs de GitHub: validación de formato
- Sanitización de inputs

**En el Manager**:
- Validación de tokens en cada request
- Verificación de ownership de proyectos
- Sanitización de parámetros antes de ejecutar comandos Docker

### 5. **Gestión de Secretos**

- Tokens de Roble no expuestos en frontend
- Credentials de Docker no hardcodeadas
- Variables de entorno para configuración sensible

---

## ⚡ Optimización de Recursos {#optimización}

### 1. **Límites por Contenedor**

**CPU**:
```python
cpu_period = 100000  # 100ms
cpu_quota = 50000    # 50ms → 0.5 CPU
```

**Memoria**:
```python
mem_limit = '256m'  # 256 MB RAM máximo
```

**Beneficios**:
- Evita que un contenedor consuma todos los recursos
- Garantiza fair-share entre proyectos
- Protege el host de sobrecarga

### 2. **Auto-Apagado de Contenedores Inactivos**

**Política**:
- Inactividad > 30 minutos → contenedor se detiene
- Contenedor detenido NO se elimina (imagen + datos persisten)
- Al recibir nueva petición → reinicio automático

**Ahorro de recursos**:
- RAM liberada inmediatamente
- CPU disponible para contenedores activos
- Disco sin duplicación (imagen compartida)

### 3. **Gestión Eficiente de Puertos**

**Estrategia**:
- Pool de puertos: 7000-7999 (1000 puertos disponibles)
- Asignación dinámica al crear proyecto
- Liberación inmediata al eliminar proyecto
- Reutilización de puertos liberados

### 4. **Clonación Shallow de Repositorios**

```bash
git clone --depth 1 <repo_url>
```

**Beneficios**:
- Solo clona último commit (no historial completo)
- Reduce tiempo de clone ~10x
- Ahorra ancho de banda y disco

### 5. **Build Cache de Docker**

- Docker reutiliza layers entre builds
- Templates con estructura similar comparten base
- Rebuild de proyectos aprovecha cache

### 6. **Cleanup Automático**

- Eliminación de imágenes huérfanas
- Cleanup de directorios temporales post-build
- Garbage collection de contenedores stopped

---

## 🛠️ Tecnologías Utilizadas {#tecnologías}

### Backend
- **Python 3.11**: Lenguaje principal
- **Flask 2.2.5**: Framework web REST API
- **Docker SDK for Python**: Gestión de contenedores
- **Requests**: HTTP client para Roble API

### Frontend
- **HTML5 / CSS3**: Estructura y estilos
- **Vanilla JavaScript**: Lógica de UI (sin frameworks)
- **Fetch API**: Comunicación con backend

### Infraestructura
- **Docker Engine**: Containerización
- **Docker Compose**: Orquestación de servicios
- **Nginx Alpine**: Reverse proxy
- **Git**: Control de versiones y clonación de repos

### Networking
- **Bridge Network**: Red personalizada Docker
- **DNS interno**: Resolución de nombres entre contenedores
- **Port mapping**: Exposición selectiva de puertos

### Monitoreo
- **Python Threading**: Activity monitor en background
- **Docker Events**: Detección de cambios de estado
- **Logging**: Python logging module

---

## 📊 Métricas del Sistema

### Capacidad
- **Máximo de proyectos simultáneos**: 1000 (pool de puertos)
- **Usuarios concurrentes**: Limitado por recursos del host
- **Proyectos por usuario**: Sin límite (configurable)

### Performance
- **Tiempo de deploy**: 30-90 segundos (depende del template)
- **Tiempo de rebuild**: 10-30 segundos (aprovecha cache)
- **Tiempo de auto-reinicio**: 3-5 segundos

### Recursos por Proyecto
- **RAM**: 256 MB (límite hard)
- **CPU**: 0.5 cores (límite hard)
- **Disco**: Variable (según proyecto, típicamente < 100 MB)

---

## 🔍 Monitoreo y Debugging

### Logs
```bash
# Ver logs del manager
docker-compose logs -f manager

# Ver logs de nginx
docker-compose logs -f nginx_proxy

# Ver logs de un proyecto específico
docker logs project_usuario_nombre
```

### Health Checks
- Dashboard auto-refresh cada 5s detecta proyectos caídos
- Activity monitor verifica estado cada 60s
- Nginx detecta backends no disponibles (502)

### Troubleshooting
- Ver `TESTING.md` para escenarios comunes
- Dashboard muestra logs de build en tiempo real
- Panel de proyectos indica estado (running/stopped/error)

---

## 📝 Conclusiones

Este sistema implementa una plataforma de hosting completa y escalable usando arquitectura de microservicios containerizada. Las estrategias de optimización (auto-apagado, rate limiting, resource limits) garantizan un uso eficiente de recursos mientras se mantiene alta disponibilidad mediante auto-reinicio.

La integración con Roble proporciona autenticación robusta, y el sistema de templates facilita el onboarding de nuevos usuarios. La arquitectura modular permite extender funcionalidad sin afectar componentes existentes.

---

**Documento generado para**: Proyecto Final - Estructura del Computador II  
**Universidad del Norte** - 2025
