# Plantillas de Proyectos - ROBLE Host

Este directorio contiene plantillas base preconfiguradas que los usuarios pueden utilizar para desplegar proyectos rápidamente en la plataforma ROBLE Host.

##  ¿Cómo usar estos templates?

### Instrucciones Paso a Paso

1. **Elige un template** según tu proyecto:
   - `static_template/` → Para sitios web estáticos (HTML/CSS/JS)
   - `react_template/` → Para aplicaciones React simples
   - `flask_template/` → Para APIs o apps Python con Flask

2. **Crea un nuevo repositorio en GitHub**
   - Ve a: https://github.com/new
   - Nombre: `mi-proyecto` (o como quieras llamarlo)
   - Público o privado (ambos funcionan)
   -  Clic en "Create repository"

3. **Copia los archivos del template a tu repositorio**
   
   **Opción A - Desde la web de GitHub:**
   - En tu nuevo repo, clic en "Add file" → "Create new file"
   - Copia el contenido de cada archivo del template
   - Ejemplo: crea `index.html` y pega el contenido de `static_template/index.html`
   - Repite para todos los archivos (incluido el `Dockerfile`)
   - Haz commit

   **Opción B - Desde la terminal:**
   ```bash
   # Clonar tu nuevo repo vacío
   git clone https://github.com/TU_USUARIO/mi-proyecto.git
   cd mi-proyecto
   
   # Copiar archivos del template que elegiste
   # (Asumiendo que clonaste host_roble)
   cp ../host_roble/templates/static_template/* .
   
   # Hacer commit y push
   git add .
   git commit -m "Initial commit from static template"
   git push
   ```

4. **Personaliza el contenido**
   - Edita los archivos según tus necesidades
   - Cambia textos, colores, código, etc.
   - Haz commit de tus cambios

5. **Despliega en ROBLE Host**
   - Abre el dashboard: `http://localhost:8080`
   - Inicia sesión con tu cuenta de Roble
   - Clic en "Nuevo Proyecto"
   - Completa el formulario:
     - **Nombre**: `mi-proyecto` (sin espacios, solo letras minúsculas y guiones)
     - **URL del repositorio**: `https://github.com/TU_USUARIO/mi-proyecto`
   - Clic en "Crear Proyecto"

6. **¡Listo! Tu proyecto estará disponible en:**
   - `http://mi-proyecto.tuUsuario.localhost`
   - También en el puerto directo que se muestra en el dashboard

---

##  Templates Disponibles

### 1.  Plantilla Estática (`static_template`)

**Descripción**: Sitio web estático básico servido con Nginx.

**Estructura**:
```
static_template/
├── index.html       # Página HTML estática
└── Dockerfile       # Imagen nginx:alpine
```

**Uso recomendado**: Landing pages, portafolios, documentación estática.

**Puerto interno**: 80

**Instrucciones detalladas**: Ver la página de templates en el dashboard (`http://localhost:8080/templates.html`)

---

### 2.  Plantilla React (`react_template`)

**Descripción**: Aplicación React completa con Vite. Build multi-stage que compila el proyecto y genera una versión estática optimizada.

**Estructura**:
```
react_template/
├── src/
│   ├── App.jsx          # Componente principal
│   ├── App.css          # Estilos del componente
│   ├── main.jsx         # Punto de entrada
│   └── index.css        # Estilos globales
├── index.html           # HTML principal
├── package.json         # Dependencias (React 18, Vite)
├── vite.config.js       # Configuración de Vite
└── Dockerfile           # Build multi-stage (Node.js → Nginx)
```

**Uso recomendado**: Aplicaciones React modernas, SPAs completas, dashboards, apps interactivas.

**Puerto interno**: 80 (Nginx sirve los archivos compilados)

**Características**:
- ⚡ Desarrollo rápido con Vite HMR
- 🐳 Dockerfile multi-stage (compila y optimiza automáticamente)
- 📦 Build estático minificado servido con Nginx
- 🚀 Imagen final ligera (~25MB)

**Nota**: El Dockerfile se encarga de todo el proceso de build automáticamente. No necesitas instalar Node.js localmente para desplegar.

**Instrucciones detalladas**: Ver `react_template/README.md` o la página de templates en el dashboard (`http://localhost:8080/templates.html`)

---

### 3.  Plantilla Flask (`flask_template`)

**Descripción**: API REST básica con Flask y Gunicorn.

**Estructura**:
```
flask_template/
├── app.py              # Aplicación Flask mínima
├── requirements.txt    # Flask==2.2.5, gunicorn==20.1.0
└── Dockerfile          # Imagen python:3.11-slim
```

**Uso recomendado**: APIs REST, microservicios Python, backends simples.

**Puerto interno**: 5000

**Instrucciones detalladas**: Ver la página de templates en el dashboard (`http://localhost:8080/templates.html`)

---

##  Acceso Rápido

Para ver los templates con código completo listo para copiar, abre:

** [Página de Templates en el Dashboard](http://localhost:8080/templates.html)**

Esta página incluye:
-  Instrucciones paso a paso
-  Código completo de cada archivo
-  Botón para copiar cada archivo al portapapeles
-  Explicaciones de qué hace cada template

---

##  Probar Localmente (Opcional)

Si quieres probar un template antes de desplegarlo:

```bash
# Plantilla Estática
cd templates/static_template
docker build -t test-static .
docker run -p 8001:80 test-static
# Abrir http://localhost:8001

# Plantilla React (tarda más por el build de Node.js)
cd templates/react_template
docker build -t test-react .
docker run -p 8002:80 test-react
# Abrir http://localhost:8002
# Nota: El build puede tardar 2-3 minutos la primera vez

# Plantilla Flask
cd templates/flask_template
docker build -t test-flask .
docker run -p 8003:5000 test-flask
# Abrir http://localhost:8003
```

### Desarrollo Local con React (Opcional)

Si quieres desarrollar localmente antes de desplegar:

```bash
cd templates/react_template
npm install
npm run dev
# Abrir http://localhost:3000
```

---

##  Consejos

- **Nombres de proyecto**: Usa solo letras minúsculas, números y guiones (sin espacios ni caracteres especiales)
- **Dockerfile obligatorio**: Todos los proyectos deben incluir un `Dockerfile` en la raíz del repositorio
- **Puertos**: Los templates usan puertos estándar (80 para nginx, 5000 para Flask). La plataforma los mapea automáticamente
- **Personalización**: Puedes modificar todo el contenido de los templates. Son solo puntos de partida
- **Updates**: Después de hacer cambios en tu repositorio, usa el botón "Rebuild" en el dashboard para actualizar tu proyecto
- **Template React**: El build multi-stage puede tardar unos minutos en el primer deploy (Node.js compila el proyecto), pero el resultado es una imagen optimizada y ligera
- **node_modules**: No subas la carpeta `node_modules` a GitHub (está en `.gitignore`). Docker la instalará automáticamente durante el build

---

##  Soporte

Si tienes problemas:
1. Verifica que tu repositorio tenga un `Dockerfile` válido
2. Revisa los logs en el dashboard después del deploy
3. Asegúrate de que el puerto interno en el Dockerfile sea el correcto
4. Consulta la documentación principal en [../README.md](../README.md)

---

**Última actualización**: 08 Noviembre 2025
