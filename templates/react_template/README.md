# Plantilla React para Roble

Esta es una plantilla completa de React con Vite optimizada para el sistema Roble.

## Características

- ⚡ **Vite**: Desarrollo rápido con Hot Module Replacement
- ⚛️ **React 18**: Última versión de React
- 🐳 **Docker Multi-stage**: Build optimizado en dos etapas
- 🚀 **Producción**: Build estático optimizado y minificado
- 📦 **Nginx**: Servidor web ligero para producción
- 🏥 **Health Checks**: Monitoreo de salud del contenedor

## Estructura del Proyecto

```
react_template/
├── src/
│   ├── App.jsx          # Componente principal
│   ├── App.css          # Estilos del componente
│   ├── main.jsx         # Punto de entrada
│   └── index.css        # Estilos globales
├── public/              # Archivos estáticos
├── index.html           # HTML principal
├── vite.config.js       # Configuración de Vite
├── package.json         # Dependencias
├── Dockerfile           # Build multi-stage
└── docker-compose.yml   # Orquestación
```

## Desarrollo Local

### Requisitos
- Node.js 18+
- npm o yarn

### Instalación
```bash
npm install
```

### Desarrollo
```bash
npm run dev
```
La aplicación estará disponible en http://localhost:3000

### Build de Producción
```bash
npm run build
```
Los archivos estáticos se generarán en la carpeta `dist/`

## Docker

### Build y Ejecución
```bash
docker-compose up -d --build
```

La aplicación estará disponible en http://localhost:8080

### Proceso de Build Docker

El Dockerfile utiliza un build multi-stage:

1. **Stage 1 (Builder)**: 
   - Usa Node.js 18 Alpine
   - Instala dependencias
   - Compila la aplicación con Vite
   - Genera archivos estáticos optimizados

2. **Stage 2 (Production)**:
   - Usa Nginx Alpine (imagen ligera)
   - Copia los archivos compilados del stage anterior
   - Expone el puerto 80
   - Incluye health check

### Beneficios del Multi-stage Build

- **Tamaño reducido**: La imagen final no incluye Node.js ni dependencias de desarrollo
- **Seguridad**: Menos superficie de ataque
- **Rendimiento**: Nginx sirve archivos estáticos de forma eficiente
- **Optimización**: Los archivos están minificados y optimizados

## Personalización

### Modificar el Componente Principal
Edita `src/App.jsx` para cambiar la interfaz de usuario.

### Añadir Rutas
Instala React Router:
```bash
npm install react-router-dom
```

### Añadir Estado Global
Instala Zustand o Redux:
```bash
npm install zustand
```

### Estilos
- CSS modules están habilitados por defecto
- Puedes usar CSS, SCSS o Tailwind CSS

## Uso en Roble

Esta plantilla está diseñada para ser desplegada automáticamente por Roble:

1. El sistema clonará esta plantilla
2. Docker construirá la imagen en dos etapas
3. Se desplegará el contenedor con Nginx sirviendo los archivos estáticos
4. El health check monitoreará el estado del servicio

## Variables de Entorno

Puedes añadir variables de entorno en tiempo de build:

1. Crea un archivo `.env`:
```
VITE_API_URL=https://api.ejemplo.com
VITE_APP_NAME=Mi App
```

2. Úsalas en tu código:
```javascript
const apiUrl = import.meta.env.VITE_API_URL
```

## Optimización

El build de producción incluye:
- Minificación de JavaScript y CSS
- Tree-shaking para eliminar código no usado
- Optimización de imágenes
- Code splitting automático
- Compresión gzip en Nginx

## Licencia

MIT
