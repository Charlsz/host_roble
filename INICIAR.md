## PARA INICIAR LA PLATAFORMA

### 1. Iniciar Docker Desktop
```
- Abrir Docker Desktop
- Esperar a que esté completamente iniciado
- Verificar que el ícono esté verde
```

### 2. Iniciar los servicios
```powershell
cd c:\Users\Cgalv\Desktop\host_roble

# Limpiar y reconstruir todo
docker-compose down -v
docker-compose up --build
```

### 3. Esperar a que todo esté listo
Verás mensajes como:
```
 Cliente Docker conectado
 Blueprints de autenticación y proyectos registrados
* Running on http://0.0.0.0:5000
```

### 4. Acceder a la plataforma
- Abrir navegador en: **http://localhost:8080**
- Verás la nueva interfaz de login/signup

---

##  PRUEBAS PASO A PASO

### Prueba 1: Registrar Usuario
1. Abrir http://localhost:8080
2. Clic en tab "Registrarse"
3. Llenar formulario:
   - Nombre: Juan Pérez
   - Email: test@uninorte.edu.co
   - Password: 123456
   - Confirmar: 123456
4. Clic "Registrarse"
5. Debe aparecer mensaje: "¡Registro exitoso! Ya puedes iniciar sesión"

### Prueba 2: Iniciar Sesión
1. Clic en tab "Iniciar Sesión"
2. Llenar:
   - Email: test@uninorte.edu.co
   - Password: 123456
3. Clic "Iniciar Sesión"
4. Debe redirigir al dashboard con mensaje de bienvenida

### Prueba 3: Crear Proyecto
1. En el dashboard, clic "Mostrar Formulario"
2. Llenar:
   - Nombre: mi-primer-sitio
   - URL: https://github.com/usuario/repo
3. Clic "Crear Proyecto"
4. El proyecto debe aparecer en "Mis Proyectos" con estado "pending"

### Prueba 4: Ver Proyecto
1. El proyecto aparece en la lista
2. Muestra:
   - Nombre
   - Estado (badge de color)
   - URL del repositorio
   - Fecha de creación
3. Botones: Reconstruir, Eliminar

### Prueba 5: Eliminar Proyecto
1. Clic en "Eliminar"
2. Confirmar en el diálogo
3. El proyecto desaparece de la lista

---

##  VERIFICAR QUE TODO FUNCIONA

### Verificar API (desde PowerShell)
```powershell
# Verificar que el manager responde
Invoke-RestMethod -Uri "http://localhost:5000/"

# Debería retornar HTML o JSON del manager
```

### Ver Logs en Tiempo Real
```powershell
# Todos los servicios
docker-compose logs -f

# Solo manager (para ver API calls)
docker-compose logs -f manager

# Solo dashboard
docker-compose logs -f dashboard
```

### Verificar Base de Datos ROBLE
```
1. Ir a tu panel ROBLE
2. Abrir sección "Tablas"
3. Verificar que existan:
   - proyectos (8 columnas)
   - containers (7 columnas)
4. Después de crear un proyecto, ver los datos en la tabla
```

---

## 🔧 SI ALGO FALLA

### Error: Docker no inicia
```powershell
# Limpiar todo
docker system prune -a -f

# Reiniciar Docker Desktop
# Esperar 1-2 minutos
# Intentar de nuevo
docker-compose up --build
```

### Error: Puerto 5000 ocupado
```powershell
# Ver qué está usando el puerto
netstat -ano | findstr :5000

# Matar el proceso
taskkill /PID <numero_pid> /F

# O cambiar puerto en docker-compose.yml
```

### Error: "Token inválido" en el dashboard
```
1. Abrir DevTools (F12)
2. Application > Local Storage
3. Borrar todo
4. Recargar página
5. Hacer login nuevamente
```

### Error: No se crean proyectos
```
1. Verificar logs: docker-compose logs manager
2. Verificar que ROBLE_CONTRACT esté correcto en .env
3. Verificar permisos en ROBLE (proyectos:insert)
4. Intentar crear manualmente en ROBLE para probar permisos
```

---

##  PRÓXIMOS PASOS

Una vez que todo funcione correctamente:

### Fase 2: Reverse Proxy
- Agregar Nginx para subdominios
- Configurar rutas dinámicas
- Probar acceso con `proyecto.usuario.localhost`

### Fase 3: GitHub Integration
- Implementar clonación de repos
- Construir imágenes Docker
- Desplegar contenedores reales

### Fase 4: Optimización
- Rate limiting
- Auto-apagado/reinicio
- Monitoreo de recursos

---

##  CHECKLIST DE VERIFICACIÓN

Antes de continuar a Fase 2, verifica que:

- [ ] Docker Desktop está corriendo
- [ ] `docker-compose up --build` ejecuta sin errores
- [ ] http://localhost:8080 abre el dashboard
- [ ] Puedes registrar un usuario nuevo
- [ ] Puedes iniciar sesión
- [ ] El dashboard muestra "Mis Proyectos"
- [ ] Puedes crear un proyecto
- [ ] El proyecto aparece en la lista
- [ ] Puedes eliminar el proyecto
- [ ] Los logs no muestran errores críticos

---