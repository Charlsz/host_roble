// Configuración de la API
const API_URL = 'http://localhost:5000/api';

// Estado de la aplicación
let currentUser = null;
let accessToken = null;
let refreshToken = null;
let projects = [];
let autoRefreshInterval = null; // Para auto-actualización

// ==================== GESTIÓN DE AUTENTICACIÓN ====================

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    // Verificar si hay sesión guardada
    const savedToken = localStorage.getItem('accessToken');
    const savedRefresh = localStorage.getItem('refreshToken');
    
    if (savedToken && savedRefresh) {
        accessToken = savedToken;
        refreshToken = savedRefresh;
        verifyAndLoadSession();
    } else {
        showAuthSection();
    }
});

async function verifyAndLoadSession() {
    try {
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            currentUser = data.user;
            showDashboard();
        } else {
            // Token inválido, limpiar y mostrar login
            clearSession();
            showAuthSection();
        }
    } catch (error) {
        console.error('Error verificando sesión:', error);
        clearSession();
        showAuthSection();
    }
}

function showAuthTab(tab) {
    // Actualizar tabs
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    
    // Mostrar contenido
    document.getElementById('login-tab').classList.toggle('hidden', tab !== 'login');
    document.getElementById('signup-tab').classList.toggle('hidden', tab !== 'signup');
}

async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    try {
        showMessage('Iniciando sesión...', 'success');
        
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Guardar tokens
            accessToken = data.accessToken;
            refreshToken = data.refreshToken;
            currentUser = data.user;
            
            localStorage.setItem('accessToken', accessToken);
            localStorage.setItem('refreshToken', refreshToken);
            
            showMessage('¡Bienvenido! Sesión iniciada correctamente', 'success');
            showDashboard();
        } else {
            showMessage(data.error || 'Error al iniciar sesión', 'error');
        }
    } catch (error) {
        console.error('Error en login:', error);
        showMessage('Error de conexión. Verifica que el servidor esté activo.', 'error');
    }
}

async function handleSignup(event) {
    event.preventDefault();
    
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const confirm = document.getElementById('signup-confirm').value;
    
    // Validar contraseñas
    if (password !== confirm) {
        showMessage('Las contraseñas no coinciden', 'error');
        return;
    }
    
    try {
        showMessage('Registrando usuario...', 'success');
        
        const response = await fetch(`${API_URL}/auth/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password, name })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('¡Registro exitoso! Ya puedes iniciar sesión', 'success');
            // Cambiar a tab de login
            document.getElementById('signup-form').reset();
            showAuthTab('login');
            document.querySelector('.auth-tab:first-child').click();
        } else {
            showMessage(data.error || 'Error al registrar usuario', 'error');
        }
    } catch (error) {
        console.error('Error en signup:', error);
        showMessage('Error de conexión. Verifica que el servidor esté activo.', 'error');
    }
}

async function logout() {
    try {
        if (accessToken) {
            await fetch(`${API_URL}/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });
        }
    } catch (error) {
        console.error('Error en logout:', error);
    } finally {
        // Detener auto-actualización
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
            autoRefreshInterval = null;
        }
        clearSession();
        showAuthSection();
        showMessage('Sesión cerrada correctamente', 'success');
    }
}

function clearSession() {
    accessToken = null;
    refreshToken = null;
    currentUser = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
}

// ==================== GESTIÓN DE PROYECTOS ====================

async function loadProjects() {
    try {
        const response = await fetch(`${API_URL}/projects/`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            projects = data.projects;
            displayProjects();
            updateStats();
        } else if (response.status === 401) {
            // Token expirado, intentar refresh
            await refreshAccessToken();
            loadProjects(); // Reintentar
        } else {
            showMessage('Error al cargar proyectos', 'error');
        }
    } catch (error) {
        console.error('Error cargando proyectos:', error);
        showMessage('Error de conexión al cargar proyectos', 'error');
    }
}

async function handleCreateProject(event) {
    event.preventDefault();
    
    const nombre = document.getElementById('project-name').value;
    const repo_url = document.getElementById('repo-url').value;
    
    try {
        showMessage('Creando proyecto...', 'success');
        
        const response = await fetch(`${API_URL}/projects/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify({ nombre, repo_url })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('¡Proyecto creado! El despliegue iniciará pronto', 'success');
            document.getElementById('create-project-form').reset();
            toggleCreateForm();
            loadProjects();
        } else {
            showMessage(data.error || 'Error al crear proyecto', 'error');
        }
    } catch (error) {
        console.error('Error creando proyecto:', error);
        showMessage('Error de conexión al crear proyecto', 'error');
    }
}

async function deleteProject(projectId, projectName) {
    if (!confirm(`¿Estás seguro de eliminar el proyecto "${projectName}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/projects/${projectId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            showMessage('Proyecto eliminado correctamente', 'success');
            loadProjects();
        } else {
            const data = await response.json();
            showMessage(data.error || 'Error al eliminar proyecto', 'error');
        }
    } catch (error) {
        console.error('Error eliminando proyecto:', error);
        showMessage('Error de conexión al eliminar proyecto', 'error');
    }
}

async function rebuildProject(projectId, projectName) {
    if (!confirm(`¿Reconstruir el proyecto "${projectName}" desde GitHub?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/projects/${projectId}/rebuild`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            showMessage('Reconstrucción iniciada', 'success');
            loadProjects();
        } else {
            const data = await response.json();
            showMessage(data.error || 'Error al reconstruir proyecto', 'error');
        }
    } catch (error) {
        console.error('Error reconstruyendo proyecto:', error);
        showMessage('Error de conexión al reconstruir proyecto', 'error');
    }
}

function displayProjects() {
    const container = document.getElementById('projects-list');
    
    if (projects.length === 0) {
        container.innerHTML = '<div class="empty-state">No tienes proyectos aún. ¡Crea tu primer proyecto!</div>';
        return;
    }
    
    container.innerHTML = projects.map(project => {
        // Usar real_status si existe, sino usar status de la BD
        const status = project.real_status || project.status;
        
        const statusClass = status === 'running' ? 'status-running' : 
                          status === 'exited' || status === 'stopped' ? 'status-stopped' : 
                          status === 'building' ? 'status-building' : 
                          status === 'pending' ? 'status-pending' : 
                          status === 'not_found' ? 'status-error' : 'status-error';
        
        // Traducir estados
        const statusText = status === 'running' ? 'corriendo' :
                          status === 'exited' ? 'detenido' :
                          status === 'building' ? 'construyendo' :
                          status === 'pending' ? 'pendiente' :
                          status === 'not_found' ? 'no encontrado' : status;
        
        // URL desde el backend
        const url = project.url;
        const url_direct = project.url_direct;
        const subdomain = project.subdomain;
        
        // Info de inactividad
        const inactiveMinutes = project.inactive_minutes || 0;
        const inactiveWarning = inactiveMinutes > 20 ? ' ⚠️ Se apagará pronto' : '';
        const inactiveDisplay = status === 'running' ? `<p><strong>Inactivo:</strong> ${inactiveMinutes} min${inactiveWarning}</p>` : '';
        
        return `
            <div class="project-card">
                <div class="project-header">
                    <h4>${project.nombre}</h4>
                    <span class="project-status ${statusClass}">${statusText}</span>
                </div>
                <div class="project-body">
                    <p><strong>Repositorio:</strong> <a href="${project.repo_url}" target="_blank">${project.repo_url}</a></p>
                    ${subdomain ? `<p><strong>Subdominio:</strong> <a href="${url}" target="_blank" class="btn-link" onclick="trackActivity('${project.container_name}')">${subdomain}</a></p>` : ''}
                    ${url_direct ? `<p><strong>URL Directa:</strong> <a href="${url_direct}" target="_blank" class="btn-link" onclick="trackActivity('${project.container_name}')">${url_direct}</a></p>` : ''}
                    ${project.external_port ? `<p><strong>Puerto:</strong> ${project.external_port}</p>` : ''}
                    ${inactiveDisplay}
                    <p><strong>Creado:</strong> ${new Date(project.created_at).toLocaleString()}</p>
                </div>
                <div class="project-actions">
                    ${url ? `<a href="${url}" target="_blank" class="btn btn-secondary" onclick="trackActivity('${project.container_name}')">Abrir Sitio</a>` : ''}
                    <button onclick="rebuildProject('${project._id}', '${project.nombre}')" class="btn btn-secondary">Reconstruir</button>
                    <button onclick="deleteProject('${project._id}', '${project.nombre}')" class="btn btn-danger">Eliminar</button>
                </div>
            </div>
        `;
    }).join('');
}

function updateStats() {
    const total = projects.length;
    // Usar real_status si existe, sino status
    const running = projects.filter(p => {
        const status = p.real_status || p.status;
        return status === 'running';
    }).length;
    const stopped = projects.filter(p => {
        const status = p.real_status || p.status;
        return status === 'stopped' || status === 'exited';
    }).length;
    
    document.getElementById('total-projects').textContent = total;
    document.getElementById('running-projects').textContent = running;
    document.getElementById('stopped-projects').textContent = stopped;
}

// ==================== HELPERS ====================

function useTemplate(template) {
    const templates = {
        'static': 'https://github.com/tu-usuario/template-static-site',
        'react': 'https://github.com/tu-usuario/template-react-app',
        'flask': 'https://github.com/tu-usuario/template-flask-blog'
    };
    
    document.getElementById('repo-url').value = templates[template] || '';
    showMessage(`Template "${template}" seleccionado. Clona este repo y personalízalo.`, 'success');
}

function getUsernameFromEmail() {
    if (!currentUser || !currentUser.email) return 'usuario';
    return currentUser.email.split('@')[0].toLowerCase().replace(/[^a-z0-9]/g, '');
}

async function refreshAccessToken() {
    try {
        const response = await fetch(`${API_URL}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refreshToken })
        });
        
        if (response.ok) {
            const data = await response.json();
            accessToken = data.accessToken;
            localStorage.setItem('accessToken', accessToken);
        } else {
            clearSession();
            showAuthSection();
        }
    } catch (error) {
        console.error('Error refrescando token:', error);
        clearSession();
        showAuthSection();
    }
}

function toggleCreateForm() {
    const form = document.getElementById('create-form');
    const btn = document.getElementById('toggle-create-btn');
    
    form.classList.toggle('hidden');
    btn.textContent = form.classList.contains('hidden') ? 
        'Mostrar Formulario' : 'Ocultar Formulario';
}

function showAuthSection() {
    document.getElementById('auth-section').classList.remove('hidden');
    document.getElementById('dashboard-section').classList.add('hidden');
    document.getElementById('user-info').classList.add('hidden');
}

function showDashboard() {
    document.getElementById('auth-section').classList.add('hidden');
    document.getElementById('dashboard-section').classList.remove('hidden');
    document.getElementById('user-info').classList.remove('hidden');
    
    // Mostrar info del usuario
    if (currentUser) {
        document.getElementById('user-email').textContent = currentUser.email || currentUser.uid || 'Usuario';
    }
    
    // Cargar proyectos
    loadProjects();
    
    // Iniciar auto-actualización cada 5 segundos
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    autoRefreshInterval = setInterval(() => {
        loadProjects();
    }, 5000);
}

// Función para registrar actividad de un contenedor
async function trackActivity(containerName) {
    if (!containerName) return;
    
    try {
        await fetch(`${API_URL}/api/projects/activity/${containerName}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        // No mostrar mensaje, es transparente para el usuario
    } catch (error) {
        console.log('Error tracking activity:', error);
        // No fallar, solo logear
    }
}

function showMessage(message, type) {
    const msgElement = type === 'error' ? 
        document.getElementById('error-msg') : 
        document.getElementById('success-msg');
    
    msgElement.textContent = message;
    msgElement.classList.remove('hidden');
    
    setTimeout(() => {
        msgElement.classList.add('hidden');
    }, 5000);
}
