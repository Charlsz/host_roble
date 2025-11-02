# Hosting ROBLE Platform

Plataforma de hosting de páginas web basada en contenedores Docker. Permite a usuarios autenticados con Roble desplegar sitios web desde repositorios de GitHub con subdominios automáticos y gestión de recursos.

## 🚀 Características

- ✅ Autenticación mediante Roble
- ✅ Deploy automático desde GitHub
- ✅ Subdominios dinámicos: `http://proyecto.usuario.localhost`
- ✅ Gestión automática de recursos (CPU/RAM limits, rate limiting)
- ✅ Auto-apagado tras 30 minutos de inactividad
- ✅ Auto-reinicio al recibir nuevas peticiones
- ✅ Dashboard web para gestión de proyectos
- ✅ Reverse proxy con Nginx

## 📦 Templates Disponibles

Los siguientes templates dockerizados están listos para ser clonados, modificados y desplegados:

### Enlaces a Templates:

1. **[Template Estático](https://github.com/Charlsz/host_roble/tree/main/templates/static_template)** - Sitio estático (HTML + CSS + JS)
   - Incluye: `index.html`, `Dockerfile`, `docker-compose.yml`
   - Puerto: 80 (Nginx)

2. **[Template React](https://github.com/Charlsz/host_roble/tree/main/templates/react_template)** - React con CDN (sin build)
   - Incluye: `index.html`, `Dockerfile`, `docker-compose.yml`
   - Puerto: 80 (Nginx)

3. **[Template Flask](https://github.com/Charlsz/host_roble/tree/main/templates/flask_template)** - Python + Flask + Gunicorn
   - Incluye: `app.py`, `requirements.txt`, `Dockerfile`, `docker-compose.yml`
   - Puerto: 5000 (Gunicorn)

📖 **Instrucciones completas**: [templates/README.md](./templates/README.md) | 🎯 **Guía visual**: [Página de Templates](http://localhost:8080/templates.html)

## 🏗️ Arquitectura

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Dashboard  │─────▶│   Manager   │─────▶│    Roble    │
│  (puerto 80)│      │ (puerto 5000│      │  (Auth API) │
└─────────────┘      └─────────────┘      └─────────────┘
                            │
                            ▼
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
                            ▲
                            │
                     ┌─────────────┐
                     │Nginx Proxy  │
                     │(puerto 80)  │
                     │Subdomain    │
                     │routing      │
                     └─────────────┘
```

### Componentes

- **Dashboard**: Interfaz web para usuarios (JavaScript vanilla)
- **Manager**: API Flask para gestión de proyectos y deploy
- **Nginx Proxy**: Reverse proxy con configuración dinámica
- **Activity Monitor**: Servicio de monitoreo de inactividad
- **Roble Client**: Integración con sistema de autenticación

## 🛠️ Instalación y Uso

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

1. Abrir dashboard: `http://localhost:8080`
2. Iniciar sesión con credenciales de Roble
3. Crear nuevo proyecto proporcionando:
   - Nombre del proyecto
   - URL del repositorio GitHub
   - Branch (opcional, default: main)

## 📝 Flujo de Uso

### Para estudiantes/usuarios:

1. **Seleccionar template**
   - Navegar a [templates/](./templates/)
   - Elegir el template que se ajuste a tu necesidad

2. **Clonar y personalizar**
   ```bash
   # Copiar archivos del template a tu repo
   # Modificar contenido según tus necesidades
   git add .
   git commit -m "Personalizar proyecto"
   git push
   ```

3. **Desplegar**
   - Dashboard → "Nuevo Proyecto"
   - Ingresar URL de tu repositorio
   - Click "Crear y Desplegar"

4. **Acceder**
   - Tu proyecto estará en: `http://nombreProyecto.tuUsuario.localhost`
   - También disponible en: `http://localhost:PUERTO_ASIGNADO`

## 🔒 Gestión de Recursos

### Límites por contenedor

- **CPU**: 0.5 cores (50% de 1 CPU)
- **RAM**: 256 MB
- **Rate Limiting**: 100 peticiones/minuto por IP

### Auto-apagado

- Contenedores inactivos por >30 minutos se detienen automáticamente
- Se reinician automáticamente al recibir una nueva petición
- El dashboard muestra tiempo de inactividad en tiempo real

## 🧪 Testing

Ver guía completa de pruebas en [TESTING.md](./TESTING.md)

### Prueba rápida

```bash
# Verificar servicios corriendo
docker-compose ps

# Ver logs del manager
docker-compose logs -f manager

# Probar un template localmente
cd templates/static_template
docker build -t test-static .
docker run -p 8001:80 test-static
# Abrir http://localhost:8001
```

## 📚 Documentación Técnica

### Estructura del Proyecto

```
host_roble/
├── manager/                 # API Flask principal
│   ├── manager.py          # Entry point
│   ├── auth_routes.py      # Rutas de autenticación
│   ├── projects_routes.py  # CRUD de proyectos
│   ├── deploy_service.py   # Servicio de deploy
│   ├── activity_monitor.py # Monitor de inactividad
│   └── roble_client.py     # Cliente API Roble
├── dashboard/              # Frontend web
│   ├── src/
│   │   ├── index.html
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── Dockerfile
├── nginx/                  # Reverse proxy
│   ├── nginx.conf
│   └── conf.d/            # Configs dinámicas
├── templates/             # Templates base
│   ├── static_template/
│   ├── react_template/
│   ├── flask_template/
│   └── README.md
├── microservices/        # Microservicios auxiliares
│   ├── aggregate_service/
│   └── filter_service/
└── docker-compose.yml    # Orquestación

```

### APIs

#### Manager API (puerto 5000)

```
POST   /api/auth/login              # Autenticación
POST   /api/auth/register           # Registro
GET    /api/projects                # Listar proyectos del usuario
POST   /api/projects                # Crear y desplegar proyecto
DELETE /api/projects/<id>           # Eliminar proyecto
POST   /api/projects/<id>/rebuild   # Reconstruir proyecto
POST   /api/projects/activity/<name> # Registrar actividad
```

## 🎥 Video de Demostración

**[Ver Video en YouTube](PENDIENTE_AGREGAR_ENLACE)**

El video muestra:
- Registro e inicio de sesión con Roble
- Selección de template y clonación a repositorio propio
- Creación y despliegue de un proyecto desde GitHub
- Acceso al proyecto mediante subdomain
- Funcionamiento de la gestión de recursos (rate limiting)
- Auto-apagado tras 30 minutos de inactividad
- Auto-reinicio automático al recibir nueva petición

**Duración**: ~7 minutos

---

## 📄 Documentación Técnica

Para información técnica detallada sobre arquitectura, flujo de trabajo y estrategias de seguridad, consulta:

**👉 [Documento Técnico Completo](./DOCUMENTACION_TECNICA.md)** (PENDIENTE)

Incluye:
- Descripción detallada de arquitectura y componentes
- Diagramas de flujo del sistema
- Estrategia de seguridad y rate limiting
- Optimización de recursos y políticas de auto-apagado

---

## 👥 Equipo

**Integrantes del Proyecto:**

- [Nombre Integrante 1] - [Rol/Responsabilidad]
- [Nombre Integrante 2] - [Rol/Responsabilidad]
- [Nombre Integrante 3] - [Rol/Responsabilidad]
- [Agregar más según el equipo...]

**Curso**: Estructura del Computador II  
**Universidad del Norte**  
**Año**: 2025

## 📄 Licencia y Autorización

Al presentar este proyecto, los integrantes del equipo autorizan expresamente que la solución (total o parcial) pueda ser utilizada por Roble como base para ofrecer servicios de hosting académicos o institucionales en el futuro, con reconocimiento público de autoría.

## 🔧 Comandos Útiles

```bash
# Limpiar sistema Docker
docker system prune -a -f

# Reconstruir todo desde cero
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Ver logs en tiempo real
docker-compose logs -f

# Entrar a un contenedor
docker exec -it host_roble_manager_1 /bin/bash

# Verificar red Docker
docker network inspect host_roble_microservices_network
```

## 🐛 Troubleshooting

### Subdomain no funciona

Verificar que el contenedor esté en la red correcta:
```bash
docker inspect project_usuario_nombre | grep NetworkMode
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
