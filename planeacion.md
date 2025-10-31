# Planificación del Proyecto Hosting - Estructura del Computador II

## Objetivo General
Transformar la plataforma actual de microservicios ROBLE en una **Plataforma de Hosting Basada en Contenedores** que permita a usuarios autenticados desplegar sitios web desde repositorios de GitHub.

---

## Estado Actual vs Objetivo

### Lo que ya tenemos:
- Sistema de gestión de contenedores Docker
- Dashboard web funcional
- Integración básica con ROBLE
- Manager con Docker SDK
- Arquitectura de microservicios
- Sistema de limpieza automática

### Lo que necesitamos agregar:
- Autenticación completa de usuarios
- Reverse Proxy con subdominios
- Integración con GitHub
- Control de recursos y rate limiting
- Templates dockerizados
- Base de datos para persistencia
- Sistema de auto-apagado/reinicio

---

## FASE 1: Autenticación y Base de Datos (Semana 1-2)

### Objetivos:
- Sistema completo de autenticación con Roble
- Base de datos para usuarios y proyectos
- Gestión de sesiones

### Tareas:

#### 1.1 Base de Datos
- [ ] Instalar PostgreSQL o MongoDB como servicio Docker
- [ ] Diseñar esquema de base de datos:
  ```
  - Tabla: usuarios (id, username, email, roble_id, created_at)
  - Tabla: proyectos (id, user_id, nombre, repo_url, container_id, status, created_at, last_access)
  - Tabla: containers (id, project_id, port, status, cpu_limit, memory_limit)
  ```
- [ ] Crear migraciones iniciales
- [ ] Implementar modelos/ORM (SQLAlchemy o similar)

#### 1.2 Sistema de Autenticación
- [ ] Implementar OAuth2/OIDC con Roble
- [ ] Crear endpoints de login/logout
- [ ] Implementar JWT para sesiones
- [ ] Middleware de autenticación
- [ ] Sistema de refresh tokens
- [ ] Proteger rutas del dashboard

#### 1.3 API de Usuarios
- [ ] `POST /api/auth/login` - Login con Roble
- [ ] `POST /api/auth/logout` - Cerrar sesión
- [ ] `GET /api/auth/me` - Info del usuario actual
- [ ] `GET /api/users/projects` - Listar proyectos del usuario

### Entregables:
- Base de datos funcional con esquema completo
- Sistema de login/logout operativo
- Dashboard actualizado con autenticación

### Responsable sugerido: 
**1 persona** - Experiencia en backend y bases de datos

---

## FASE 2: Reverse Proxy y Subdominios (Semana 2-3)

### Objetivos:
- Implementar reverse proxy (Nginx o Traefik)
- Soporte para subdominios dinámicos
- Enrutamiento automático a contenedores

### Tareas:

#### 2.1 Configuración de Reverse Proxy
- [ ] Agregar servicio Nginx/Traefik al docker-compose
- [ ] Configurar wildcard DNS local (*.localhost)
- [ ] Implementar template de configuración dinámica
- [ ] Configurar red Docker compartida

#### 2.2 Gestión Dinámica de Rutas
- [ ] API para registrar nuevos subdominios
- [ ] Script de recarga de configuración Nginx
- [ ] Sistema de mapeo: `proyecto.usuario.localhost` → `container:port`
- [ ] Manejo de errores (404, 502)

#### 2.3 Integración con Manager
- [ ] Modificar `manager.py` para registrar rutas
- [ ] Endpoint para actualizar proxy al crear contenedor
- [ ] Endpoint para limpiar rutas al eliminar contenedor
- [ ] Logs de acceso por proyecto

### Estructura esperada:
```
http://miapp.juan.localhost → Container juan_miapp (port 3000)
http://blog.maria.localhost → Container maria_blog (port 8080)
```

### Entregables:
- Reverse proxy funcional
- Sistema de subdominios dinámicos
- Documentación de configuración DNS local

### Responsable sugerido:
**1 persona** - Experiencia en redes y configuración de servidores

---

## FASE 3: Integración con GitHub (Semana 3-4)

### Objetivos:
- Clonar repositorios de usuarios
- Construir imágenes Docker desde repos
- Desplegar contenedores automáticamente

### Tareas:

#### 3.1 Sistema de Clonación
- [ ] Implementar clonación segura de repos (GitPython o subprocess)
- [ ] Validación de repositorios (existencia, permisos públicos)
- [ ] Manejo de repositorios privados (opcional: tokens de acceso)
- [ ] Limpieza de repos temporales

#### 3.2 Builder de Imágenes
- [ ] Detectar Dockerfile en el repositorio
- [ ] Construir imagen Docker desde repo clonado
- [ ] Tag de imágenes: `user_project:latest`
- [ ] Logs de construcción en tiempo real
- [ ] Manejo de errores de build

#### 3.3 API de Proyectos
- [ ] `POST /api/projects/create`
  - Parámetros: `name`, `repo_url`, `template` (opcional)
  - Valida repo → Clona → Build → Deploy
- [ ] `GET /api/projects/:id` - Info del proyecto
- [ ] `DELETE /api/projects/:id` - Eliminar proyecto
- [ ] `POST /api/projects/:id/rebuild` - Reconstruir desde GitHub

#### 3.4 Proceso de Despliegue
```
1. Usuario provee URL de GitHub y nombre
2. Sistema valida y clona repo
3. Verifica existencia de Dockerfile
4. Construye imagen Docker
5. Crea contenedor con límites de recursos
6. Registra subdominio en proxy
7. Guarda info en base de datos
8. Retorna URL de acceso
```

### Entregables:
- Sistema completo de clonación y build
- API de gestión de proyectos
- Despliegue automático funcional

### Responsable sugerido:
**1-2 personas** - Experiencia en Git, Docker y Python

---

## FASE 4: Control de Recursos y Rate Limiting (Semana 4-5)

### Objetivos:
- Limitar recursos por contenedor
- Rate limiting de peticiones
- Auto-apagado por inactividad
- Auto-reinicio al recibir tráfico

### Tareas:

#### 4.1 Límites de Recursos Docker
- [ ] Configurar `--cpus=0.5` (50% de 1 CPU)
- [ ] Configurar `--memory=256m` (256 MB RAM)
- [ ] Aplicar límites al crear contenedores
- [ ] Monitoreo de uso de recursos

#### 4.2 Rate Limiting
- [ ] Instalar Redis como servicio
- [ ] Implementar middleware de rate limiting
- [ ] Configurar: 60 requests/minuto por IP
- [ ] Respuestas HTTP 429 (Too Many Requests)
- [ ] Dashboard para ver métricas

#### 4.3 Sistema de Auto-Apagado
- [ ] Crear servicio `monitor_service`:
  - Revisa cada 5 minutos contenedores activos
  - Verifica último acceso en base de datos
  - Detiene contenedores inactivos >30 min
  - Mantiene estado "sleeping" en DB
- [ ] Actualizar timestamp en cada petición al proxy

#### 4.4 Sistema de Auto-Reinicio
- [ ] Modificar Nginx para detectar contenedores detenidos
- [ ] Script de reinicio automático:
  - Proxy recibe petición
  - Si contenedor está detenido (502/503)
  - Manager recibe señal de reinicio
  - Espera a que contenedor esté listo
  - Reintenta la petición
- [ ] Timeout de 30 segundos para reinicio

### Configuración de contenedores:
```yaml
docker run -d \
  --name user_project \
  --cpus="0.5" \
  --memory="256m" \
  --restart=no \
  -p 3000:3000 \
  user_project:latest
```

### Entregables:
- Rate limiting funcional
- Auto-apagado operativo
- Auto-reinicio implementado
- Dashboard con métricas de recursos

### Responsable sugerido:
**1 persona** - Experiencia en optimización y monitoreo

---

## FASE 5: Templates Dockerizados (Semana 5-6)

### Objetivos:
- Crear 3 templates base funcionales
- Dockerizar cada template
- Publicar en repositorios GitHub separados

### Tareas:

#### 5.1 Template 1: Sitio Estático (HTML + CSS + JS)
- [ ] Crear proyecto base con:
  - `index.html`, `style.css`, `app.js`
  - Ejemplo: Portfolio personal
- [ ] Dockerfile con Nginx
- [ ] README con instrucciones
- [ ] Publicar en GitHub: `template-static-site`

#### 5.2 Template 2: React App
- [ ] Crear app React con `create-react-app` o Vite
- [ ] Ejemplo: Dashboard simple
- [ ] Dockerfile multi-stage:
  - Stage 1: Build con Node
  - Stage 2: Serve con Nginx
- [ ] README con instrucciones
- [ ] Publicar en GitHub: `template-react-app`

#### 5.3 Template 3: Flask (Python)
- [ ] Crear app Flask con:
  - Templates HTML (Jinja2)
  - Static files (CSS/JS)
  - Ejemplo: Blog simple con posts
- [ ] Dockerfile con Python + Gunicorn
- [ ] `requirements.txt`
- [ ] README con instrucciones
- [ ] Publicar en GitHub: `template-flask-blog`

#### 5.4 Sistema de Templates en Plataforma
- [ ] Página de "Nuevo Proyecto" con templates
- [ ] Botón "Usar Template" que:
  - Muestra URL del template
  - Permite clonar a repo personal del usuario
  - Pre-llena el formulario con URL
- [ ] Documentación de cómo modificar templates

### Estructura de cada template:
```
template-xxx/
├── README.md           # Instrucciones completas
├── Dockerfile          # Build instructions
├── docker-compose.yml  # Para pruebas locales
├── .dockerignore
└── src/                # Código fuente
```

### Entregables:
- 3 repositorios GitHub públicos
- Templates completamente funcionales
- Documentación de uso
- Integración en el dashboard

### Responsable sugerido:
**1-2 personas** - Experiencia en frontend y diferentes frameworks

---

## FASE 6: Documentación y Testing (Semana 6-7)

### Objetivos:
- Documentación completa
- Video de demostración
- Testing de la plataforma
- Documento técnico

### Tareas:

#### 6.1 Documentación Técnica
- [ ] Actualizar README.md principal:
  - Descripción del proyecto
  - Arquitectura completa
  - Instrucciones de instalación
  - Guía de uso
- [ ] Documento técnico (PDF):
  - Arquitectura y componentes
  - Diagramas de flujo
  - Estrategia de seguridad
  - Optimización de recursos
  - Decisiones de diseño

#### 6.2 Video de Demostración
- [ ] Script del video:
  1. Registro e inicio de sesión (2 min)
  2. Exploración de templates (1 min)
  3. Creación de proyecto desde GitHub (3 min)
  4. Acceso al sitio desplegado (1 min)
  5. Demostración de rate limiting (1 min)
  6. Auto-apagado tras inactividad (2 min)
  7. Auto-reinicio al acceder (1 min)
  8. Dashboard de administración (2 min)
- [ ] Grabar video (10-15 minutos)
- [ ] Editar y subir a YouTube
- [ ] Agregar subtítulos/anotaciones

#### 6.3 Testing
- [ ] Pruebas de registro/login
- [ ] Pruebas de creación de proyectos
- [ ] Pruebas con los 3 templates
- [ ] Pruebas de rate limiting
- [ ] Pruebas de auto-apagado/reinicio
- [ ] Pruebas de límites de recursos
- [ ] Pruebas de múltiples usuarios simultáneos

#### 6.4 Preparación de Entrega
- [ ] README principal actualizado
- [ ] Links a templates en README
- [ ] Link a video en README
- [ ] Documento técnico en carpeta `/docs`
- [ ] Verificar todos los requisitos del proyecto
- [ ] Inscripción en catálogo y planilla

### Entregables:
- README completo
- Video en YouTube
- Documento técnico
- Proyecto listo para entregar

### Responsable sugerido:
**Todo el equipo** - Participación de todos

---

## Cronograma Resumen

| Semana | Fase | Entregable Principal | Horas Est. |
|--------|------|---------------------|------------|
| 1-2 | Fase 1 | Autenticación + BD | 20-25h |
| 2-3 | Fase 2 | Reverse Proxy | 15-20h |
| 3-4 | Fase 3 | Integración GitHub | 25-30h |
| 4-5 | Fase 4 | Control de Recursos | 20-25h |
| 5-6 | Fase 5 | Templates | 15-20h |
| 6-7 | Fase 6 | Documentación + Video | 15-20h |

**Total estimado: 110-140 horas** (distribuido entre 3-5 personas ≈ 25-35h por persona)

---

## Distribución Sugerida del Equipo (5 personas)

### Persona 1: Backend + Auth (Líder Técnico)
- Fase 1: Autenticación y BD
- Fase 3: API de proyectos
- Soporte general en todas las fases

### Persona 2: DevOps + Infraestructura
- Fase 2: Reverse Proxy
- Fase 4: Control de recursos y monitoreo
- Configuración de Docker Compose

### Persona 3: Integración + Git
- Fase 3: Sistema de clonación y builder
- Fase 4: Sistema de auto-apagado/reinicio
- Testing de integración

### Persona 4: Frontend + Templates
- Actualización del Dashboard (todas las fases)
- Fase 5: Template React
- Fase 5: Template estático

### Persona 5: Fullstack + Templates
- Fase 5: Template Flask
- Fase 6: Documentación técnica
- Fase 6: Video de demostración
- Testing general

---

## Criterios de Éxito

### Funcionales:
- Usuario puede registrarse con Roble
- Usuario puede crear proyecto desde GitHub
- Sitio accesible en `proyecto.usuario.localhost`
- Rate limiting funciona (60 req/min)
- Contenedores se apagan tras 30 min
- Contenedores se reinician al recibir tráfico
- Los 3 templates funcionan correctamente

### Técnicos:
- Código organizado y documentado
- Docker Compose con todos los servicios
- Base de datos persistente
- Logs centralizados
- Manejo de errores robusto

### Entrega:
- Repositorio GitHub completo
- 3 repositorios de templates
- Video de demostración en YouTube
- Documento técnico PDF
- Inscripción en catálogo completada

---

## Comandos Rápidos

### Iniciar desarrollo:
```bash
docker-compose up --build
```

### Ver logs específicos:
```bash
docker-compose logs -f manager
docker-compose logs -f proxy
```

### Limpiar todo:
```bash
docker-compose down -v
docker system prune -a
```

### Acceder a base de datos:
```bash
docker exec -it postgres_db psql -U postgres
```

---

## Notas Importantes

1. **Participación**: Cada miembro debe tener commits visibles en GitHub
2. **Documentación**: Comentar código y decisiones importantes
3. **Testing**: Probar cada fase antes de avanzar
4. **Comunicación**: Reuniones semanales de seguimiento
5. **Backups**: Hacer push frecuente a GitHub
6. **Deadline**: Día del final según programación

---

## Enlaces de Referencia

- [Documentación Docker SDK](https://docker-py.readthedocs.io/)
- [Nginx Reverse Proxy Guide](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [Flask-OIDC](https://flask-oidc.readthedocs.io/)
- [Docker Resource Constraints](https://docs.docker.com/config/containers/resource_constraints/)

---

## Checklist Final Pre-Entrega

- [ ] Todos los servicios levanten con `docker-compose up`
- [ ] Login con Roble funciona
- [ ] Se puede crear proyecto desde GitHub
- [ ] Los 3 templates se despliegan correctamente
- [ ] Subdominios funcionan (`*.usuario.localhost`)
- [ ] Rate limiting activo
- [ ] Auto-apagado funciona (probar esperar 30+ min)
- [ ] Auto-reinicio funciona
- [ ] Video subido a YouTube
- [ ] Documento técnico completo
- [ ] README actualizado con todos los links
- [ ] Equipo inscrito en catálogo
- [ ] Autorización de uso firmada

---
