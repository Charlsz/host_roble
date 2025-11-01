/**
 * Dashboard JavaScript - Microservicios ROBLE
 * VERSIÓN 2.0 - DEBUGGING COMPLETO - 10/OCT/2025
 */

console.log('🔥 NUEVO ARCHIVO JS CARGADO - VERSIÓN 2.0 🔥');

// Configuración global
const CONFIG = {
    MANAGER_URL: 'http://localhost:5000',
    REFRESH_INTERVAL: 30000 // 30 segundos
};

// Estado global de la aplicación
let currentToken = null;
let currentUser = null;
let activeServices = [];
let pendingAction = null;
let refreshTimer = null;

console.log('🚀 Dashboard ROBLE iniciado');

// ==================== UTILIDADES ====================

function showMessage(message, type = 'success') {
    hideMessages();
    const messageEl = document.getElementById(type === 'error' ? 'error-msg' : 'success-msg');
    messageEl.textContent = message;
    messageEl.classList.remove('hidden');
    
    // Auto-hide después de 5 segundos
    setTimeout(() => {
        messageEl.classList.add('hidden');
    }, 5000);
}

function showError(message) {
    showMessage(message, 'error');
}

function showSuccess(message) {
    showMessage(message, 'success');
}

function hideMessages() {
    document.getElementById('error-msg').classList.add('hidden');
    document.getElementById('success-msg').classList.add('hidden');
}

function showLoading(show = true) {
    const spinner = document.getElementById('loading-spinner');
    if (show) {
        spinner.classList.remove('hidden');
    } else {
        spinner.classList.add('hidden');
    }
}

function apiRequest(endpoint, options = {}) {
    const url = `${CONFIG.MANAGER_URL}${endpoint}`;
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(currentToken && { 'Authorization': `Bearer ${currentToken}` })
        }
    };
    
    return fetch(url, { ...defaultOptions, ...options });
}

// ==================== AUTENTICACIÓN ====================

async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    
    if (!email || !password) {
        showError('Por favor complete todos los campos');
        return;
    }
    
    showLoading(true);
    
    try {
        console.log('🔐 Iniciando login con ROBLE...');
        
        const response = await apiRequest('/api/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            currentToken = data.token;
            currentUser = email;
            
            // Guardar en localStorage
            localStorage.setItem('roble_token', currentToken);
            localStorage.setItem('roble_user', currentUser);
            
            showSuccess('Login exitoso');
            showDashboard();
            
            console.log('✅ Login exitoso');
            
        } else {
            showError(data.error || 'Error de autenticación');
            console.error('❌ Error de login:', data.error);
        }
        
    } catch (error) {
        showError('Error de conexión con el servidor');
        console.error('❌ Error de conexión:', error);
    } finally {
        showLoading(false);
    }
}

function showDashboard() {
    // Ocultar login y mostrar dashboard
    document.getElementById('login-section').classList.add('hidden');
    document.getElementById('dashboard-section').classList.remove('hidden');
    document.getElementById('user-info').classList.remove('hidden');
    document.getElementById('user-email').textContent = currentUser;
    
    // Cargar datos iniciales
    refreshServices();
    loadTestServices();
    startAutoRefresh();
}

function logout() {
    console.log('🚪 Cerrando sesión...');
    
    // Limpiar estado
    currentToken = null;
    currentUser = null;
    activeServices = [];
    
    // Limpiar localStorage
    localStorage.removeItem('roble_token');
    localStorage.removeItem('roble_user');
    
    // Limpiar timers
    if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
    }
    
    // Mostrar login
    document.getElementById('dashboard-section').classList.add('hidden');
    document.getElementById('user-info').classList.add('hidden');
    document.getElementById('login-section').classList.remove('hidden');
    
    // Limpiar formularios
    document.getElementById('login-form').reset();
    clearCreateForm();
    clearTestForm();
    hideMessages();
    
    showSuccess('Sesión cerrada correctamente');
}

// ==================== GESTIÓN DE MICROSERVICIOS ====================

let isCreatingService = false; // Flag para prevenir doble creación

async function handleCreateService(event) {
    event.preventDefault();
    
    // Prevenir doble-click o creaciones concurrentes
    if (isCreatingService) {
        console.log('⚠️ Creación ya en progreso, ignorando...');
        return;
    }
    
    isCreatingService = true;
    
    try {
        const name = document.getElementById('service-name').value.trim();
        const type = document.getElementById('service-type').value;
        const description = document.getElementById('service-description').value.trim();
        const customCode = document.getElementById('custom-code').value.trim();
        
        console.log('📝 Datos del formulario:', {
            name,
            type,
            description,
            customCodeLength: customCode.length,
            hasCustomCode: !!customCode
        });
        
        if (!name) {
            showError('El nombre del servicio es requerido');
            return;
        }
        
        // Validar nombre
        if (!/^[a-zA-Z0-9-_]+$/.test(name)) {
            showError('El nombre solo puede contener letras, números, guiones y guiones bajos');
            return;
        }
        
        // Validar código personalizado si se proporcionó
        if (customCode) {
            console.log('🔍 Código personalizado recibido (' + customCode.length + ' caracteres)');
            console.log('📄 Código:', customCode.substring(0, 100) + '...');
        } else {
            console.log('ℹ️ No se proporcionó código personalizado, se usará plantilla por defecto');
        }
        
        showLoading(true);
        
        try {
            console.log('🏗️ Creando microservicio:', { name, type, description, hasCustomCode: !!customCode });
            
            const payload = { 
                name, 
                type, 
                config: { description }
            };
            
            // Agregar código personalizado si existe
            if (customCode) {
                payload.custom_code = customCode;
                console.log('📝 Incluyendo código personalizado (' + customCode.length + ' caracteres)');
            }
            
            const response = await apiRequest('/api/microservices', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            
            console.log('📡 Respuesta del servidor:', response.status, response.statusText);
        
        // Intentar parsear la respuesta JSON
        let data;
        try {
            data = await response.json();
            console.log('📄 Datos de respuesta:', data);
        } catch (parseError) {
            console.error('❌ Error parseando respuesta JSON:', parseError);
            showError('Error: Respuesta inválida del servidor');
            return;
        }
        
        if (response.ok && data.success) {
            showSuccess(`Microservicio '${name}' creado exitosamente`);
            clearCreateForm();
            refreshServices();
            loadTestServices();
            
            console.log('✅ Microservicio creado exitosamente');
            
        } else {
            const errorMessage = data.error || data.message || `Error ${response.status}: ${response.statusText}`;
            showError(errorMessage);
            console.error('❌ Error creando microservicio:', errorMessage, data);
        }
        
        } catch (error) {
            showError('Error de conexión: ' + error.message);
            console.error('❌ Error de conexión:', error);
        } finally {
            showLoading(false);
            isCreatingService = false; // Liberar el flag
        }
    } catch (error) {
        // Captura errores en validación
        showError('Error de validación: ' + error.message);
        isCreatingService = false;
    }
}

async function deleteService(serviceId, serviceName) {
    try {
        console.log('🎯 INICIO deleteService - Parámetros recibidos:');
        console.log('   serviceId tipo:', typeof serviceId, 'valor:', serviceId);
        console.log('   serviceName tipo:', typeof serviceName, 'valor:', serviceName);
        
        // Verificar si serviceName es literalmente la cadena "null" o "undefined"
        if (serviceName === 'null' || serviceName === 'undefined') {
            console.warn('⚠️ serviceName contiene cadena literal null/undefined, corrigiendo...');
            serviceName = serviceId;
        }
        
        // Asegurar que tenemos un nombre válido
        const finalServiceName = serviceName || serviceId || 'Sin nombre';
        console.log('📝 Nombre final calculado:', finalServiceName);
        
        // Configurar acción pendiente para el modal
        pendingAction = {
            action: 'delete',
            serviceId: serviceId,
            serviceName: finalServiceName
        };
        
        console.log('📝 Acción pendiente creada:', JSON.stringify(pendingAction, null, 2));
        
        // Usar el nombre seguro directamente en lugar de acceder a pendingAction
        console.log('🖼️ Llamando showModal con título y mensaje...');
        showModal(
            'Confirmar Eliminación',
            `¿Está seguro de eliminar el microservicio '${finalServiceName}'? Esta acción no se puede deshacer.`
        );
        console.log('✅ showModal ejecutado sin errores');
        
    } catch (error) {
        console.error('❌ ERROR EN deleteService:', error);
        console.error('❌ Stack trace:', error.stack);
        showError('Error interno: ' + error.message);
    }
}

async function executeDelete() {
    try {
        console.log('🎯 INICIO executeDelete, pendingAction:', pendingAction);
        
        if (!pendingAction || pendingAction.action !== 'delete') {
            console.error('❌ No hay acción pendiente de eliminación');
            showError('Error: No se puede proceder con la eliminación');
            return;
        }
        
        // Verificar que pendingAction tenga las propiedades necesarias
        if (!pendingAction.serviceId) {
            console.error('❌ pendingAction no tiene serviceId');
            showError('Error: Datos de eliminación incompletos');
            return;
        }
        
        // Guardar datos INMEDIATAMENTE antes de cualquier operación asíncrona
        const actionData = {
            serviceId: pendingAction.serviceId,
            serviceName: pendingAction.serviceName || pendingAction.serviceId || 'Sin nombre',
            originalPendingAction: JSON.parse(JSON.stringify(pendingAction))
        };
        
        console.log('💾 Datos guardados para eliminación:', actionData);
        
        showLoading(true);
        
        try {
            console.log('🗑️ Eliminando microservicio:', actionData);
            
            const response = await apiRequest(`/api/microservices/${actionData.serviceId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                showSuccess(`Microservicio '${actionData.serviceName}' eliminado exitosamente`);
                refreshServices();
                loadTestServices(); // Actualizar lista de pruebas
                
                console.log('✅ Microservicio eliminado exitosamente');
                
            } else {
                throw new Error(data.error || 'Error desconocido eliminando microservicio');
            }
            
        } catch (networkError) {
            console.error('❌ Error de red en executeDelete:', networkError);
            showError('Error de conexión: ' + networkError.message);
        }
        
    } catch (error) {
        console.error('❌ ERROR GENERAL en executeDelete:', error);
        console.error('❌ Stack trace completo:', error.stack);
        showError('Error interno: ' + error.message);
    } finally {
        showLoading(false);
        pendingAction = null;
        console.log('🧹 pendingAction limpiado');
    }
}

async function refreshServices() {
    try {
        console.log('🔄 Actualizando lista de servicios...');
        
        const response = await apiRequest('/api/microservices');
        const data = await response.json();
        
        if (response.ok && data.microservices) {
            activeServices = data.microservices;
            renderServices(data.microservices);
            updateStats(data.microservices);
            
            // Actualizar también la lista de servicios para pruebas
            loadTestServices();
            
            console.log(`✅ ${data.microservices.length} servicios cargados`);
            
        } else {
            showError('Error cargando servicios');
            console.error('❌ Error cargando servicios:', data.error);
        }
        
    } catch (error) {
        showError('Error de conexión al cargar servicios');
        console.error('❌ Error de conexión:', error);
    }
}

function renderServices(services) {
    const container = document.getElementById('services-list');
    
    console.log('🎨 Renderizando servicios:', services.length);
    
    if (services.length === 0) {
        container.innerHTML = '<div class="loading">No hay microservicios activos</div>';
        return;
    }

    container.innerHTML = services.map((service, index) => {
        console.log(`📋 Servicio ${index}:`, JSON.stringify(service, null, 2));
        
        const statusClass = service.status === 'running' ? 'running' : 
                           service.is_static ? 'static' : 'stopped';
        
        // Sanitizar el nombre para evitar problemas con comillas
        const safeName = service.name ? service.name.replace(/'/g, "\\'") : service.id;
        const safeId = service.id ? service.id.replace(/'/g, "\\'") : '';
        
        console.log(`🔍 Para servicio ${index}: safeName="${safeName}", safeId="${safeId}"`);
        
        return `
            <div class="service-item">
                <div class="service-header">
                    <div class="service-info">
                        <h4>${service.name}</h4>
                        <p><strong>Tipo:</strong> ${service.type}</p>
                        <p><strong>Puerto:</strong> ${service.port || 'N/A'}</p>
                        <p><strong>Estado:</strong> <span class="service-status ${statusClass}">${service.status}</span></p>
                        ${service.external_endpoint ? `
                            <p><strong>URL:</strong> <a href="${service.external_endpoint}" target="_blank" class="service-link">${service.external_endpoint}</a></p>
                        ` : ''}
                        <p><strong>Creado:</strong> ${new Date(service.created_at).toLocaleString()}</p>
                        ${service.config?.description ? `
                            <p><strong>Descripción:</strong> ${service.config.description}</p>
                        ` : ''}
                    </div>
                </div>
                
                <div class="service-actions">
                    ${service.external_endpoint ? `
                        <a href="${service.external_endpoint}" target="_blank" class="btn btn-outline">
                            Ver Servicio
                        </a>
                    ` : ''}
                    ${!service.is_static ? `
                        <button onclick="deleteService('${safeId}', '${safeName}')" class="btn btn-danger">
                            Eliminar
                        </button>
                    ` : `
                        <span class="service-status static">Servicio Base</span>
                    `}
                </div>
            </div>
        `;
    }).join('');
}

function updateStats(services) {
    const totalServices = services.length;
    const runningServices = services.filter(s => s.status === 'running').length;
    const customServices = services.filter(s => !s.is_static).length;
    
    document.getElementById('total-services').textContent = totalServices;
    document.getElementById('running-services').textContent = runningServices;
    document.getElementById('custom-services').textContent = customServices;
}

// ==================== HERRAMIENTA DE PRUEBAS ====================

function loadTestServices() {
    const select = document.getElementById('test-service');
    select.innerHTML = '<option value="">Seleccione un servicio</option>';
    
    activeServices.forEach(service => {
        if (service.external_endpoint || service.endpoint) {
            const option = document.createElement('option');
            option.value = service.external_endpoint || service.endpoint;
            option.textContent = `${service.name} (${service.type})`;
            // Guardar el tipo de servicio como data attribute
            option.setAttribute('data-service-type', service.type);
            option.setAttribute('data-service-name', service.name);
            select.appendChild(option);
        }
    });
}

function updateTestEndpoint() {
    const select = document.getElementById('test-service');
    const endpoint = document.getElementById('test-endpoint');
    
    if (select.value) {
        const selectedOption = select.options[select.selectedIndex];
        const serviceType = selectedOption.getAttribute('data-service-type');
        const serviceName = selectedOption.getAttribute('data-service-name');
        
        // Establecer endpoint según el tipo de servicio
        if (serviceType === 'filter' || serviceName === 'filter-service') {
            endpoint.value = '/filter';
        } else if (serviceType === 'aggregate' || serviceName === 'aggregate-service') {
            endpoint.value = '/aggregate';
        } else {
            endpoint.value = '/process'; // Para servicios personalizados
        }
    } else {
        endpoint.value = '';
    }
}

async function testEndpoint() {
    const serviceUrl = document.getElementById('test-service').value;
    const endpoint = document.getElementById('test-endpoint').value;
    const dataText = document.getElementById('test-data').value;
    
    if (!serviceUrl) {
        showError('Seleccione un servicio');
        return;
    }
    
    let data = {};
    if (dataText.trim()) {
        try {
            data = JSON.parse(dataText);
        } catch (e) {
            showError('Datos JSON inválidos');
            return;
        }
    }
    
    const url = serviceUrl + endpoint;
    showLoading(true);
    
    try {
        console.log('🧪 Probando endpoint:', url);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentToken}`
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        const resultDiv = document.getElementById('test-result');
        const outputDiv = document.getElementById('test-output');
        
        outputDiv.innerHTML = `
            <h4>Resultado de la Prueba:</h4>
            <p><strong>URL:</strong> ${url}</p>
            <p><strong>Método:</strong> POST</p>
            <p><strong>Status:</strong> ${response.status} ${response.statusText}</p>
            <p><strong>Tiempo:</strong> ${new Date().toLocaleTimeString()}</p>
            <div class="test-output">
                <pre>${JSON.stringify(result, null, 2)}</pre>
            </div>
        `;
        
        resultDiv.classList.remove('hidden');
        
        if (response.ok) {
            showSuccess('Prueba ejecutada exitosamente');
        } else {
            showError('La prueba retornó un error');
        }
        
        console.log('✅ Prueba completada');
        
    } catch (error) {
        showError('Error ejecutando prueba: ' + error.message);
        console.error('❌ Error en prueba:', error);
    } finally {
        showLoading(false);
    }
}

// ==================== GESTIÓN DE FORMULARIOS ====================

function toggleCreateForm() {
    const form = document.getElementById('create-form');
    const btn = document.getElementById('toggle-create-btn');
    
    if (form.classList.contains('hidden')) {
        form.classList.remove('hidden');
        btn.textContent = 'Ocultar Formulario';
    } else {
        form.classList.add('hidden');
        btn.textContent = 'Mostrar Formulario';
        clearCreateForm();
    }
}

function toggleTestForm() {
    const form = document.getElementById('test-form');
    const btn = document.getElementById('toggle-test-btn');
    
    if (form.classList.contains('hidden')) {
        form.classList.remove('hidden');
        btn.textContent = 'Ocultar Herramienta';
        loadTestServices();
    } else {
        form.classList.add('hidden');
        btn.textContent = 'Mostrar Herramienta';
        clearTestForm();
    }
}

function clearCreateForm() {
    document.getElementById('create-service-form').reset();
    document.getElementById('service-name').value = '';
    document.getElementById('service-type').value = 'filter';
    document.getElementById('service-description').value = '';
    
    // Limpiar el editor de código
    const codeEditor = document.getElementById('custom-code');
    if (codeEditor) {
        codeEditor.value = '';
    }
}

function clearTestForm() {
    document.getElementById('test-service').value = '';
    document.getElementById('test-endpoint').value = '';
    document.getElementById('test-data').value = '{"criteria": "active", "limit": 10}';
    document.getElementById('test-result').classList.add('hidden');
}

// ==================== HERRAMIENTAS DE GESTIÓN ====================

function exportConfiguration() {
    const config = {
        services: activeServices,
        user: currentUser,
        exported_at: new Date().toISOString(),
        total_services: activeServices.length,
        running_services: activeServices.filter(s => s.status === 'running').length
    };
    
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `microservices_config_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    
    showSuccess('Configuración exportada exitosamente');
    console.log('📥 Configuración exportada');
}

function showSystemLogs() {
    const output = document.getElementById('management-output');
    const content = document.getElementById('management-content');
    
    const logs = [
        `[${new Date().toISOString()}] INFO: Sistema iniciado`,
        `[${new Date().toISOString()}] INFO: Usuario ${currentUser} conectado`,
        `[${new Date().toISOString()}] INFO: ${activeServices.length} microservicios activos`,
        `[${new Date().toISOString()}] INFO: Servicios: ${activeServices.map(s => s.name).join(', ')}`,
        `[${new Date().toISOString()}] INFO: Dashboard funcionando correctamente`
    ];
    
    content.innerHTML = `
        <h4>Logs del Sistema</h4>
        <div class="test-output">
            <pre>${logs.join('\n')}</pre>
        </div>
        <button onclick="hideManagementOutput()" class="btn btn-secondary" style="margin-top: 15px;">
            Cerrar
        </button>
    `;
    
    output.classList.remove('hidden');
    console.log('📋 Logs mostrados');
}

function showStatistics() {
    const output = document.getElementById('management-output');
    const content = document.getElementById('management-content');
    
    const stats = {
        total_services: activeServices.length,
        running_services: activeServices.filter(s => s.status === 'running').length,
        stopped_services: activeServices.filter(s => s.status === 'stopped').length,
        static_services: activeServices.filter(s => s.is_static).length,
        custom_services: activeServices.filter(s => !s.is_static).length,
        service_types: activeServices.reduce((acc, s) => {
            acc[s.type] = (acc[s.type] || 0) + 1;
            return acc;
        }, {}),
        last_updated: new Date().toISOString(),
        user: currentUser
    };
    
    content.innerHTML = `
        <h4>Estadísticas Detalladas</h4>
        <div class="test-output">
            <pre>${JSON.stringify(stats, null, 2)}</pre>
        </div>
        <button onclick="hideManagementOutput()" class="btn btn-secondary" style="margin-top: 15px;">
            Cerrar
        </button>
    `;
    
    output.classList.remove('hidden');
    console.log('📊 Estadísticas mostradas');
}

function hideManagementOutput() {
    document.getElementById('management-output').classList.add('hidden');
}

// ==================== MODAL ====================

function showModal(title, message) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-message').textContent = message;
    document.getElementById('modal').classList.remove('hidden');
}

function closeModal() {
    console.log('🚪 closeModal llamado, pendingAction actual:', pendingAction);
    document.getElementById('modal').classList.add('hidden');
    // No limpiar pendingAction aquí, se limpia después de ejecutar la acción
}

function confirmAction() {
    console.log('🔄 confirmAction ejecutada, pendingAction:', pendingAction);
    
    if (pendingAction && pendingAction.action === 'delete') {
        console.log('✅ Acción de eliminación confirmada');
        closeModal();
        executeDelete();
    } else {
        console.log('❌ No hay acción de eliminación válida:', pendingAction);
        closeModal();
        // Limpiar pendingAction solo si no es una acción válida
        pendingAction = null;
    }
}

// ==================== AUTO-REFRESH ====================

function startAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    
    refreshTimer = setInterval(() => {
        if (currentToken) {
            console.log('🔄 Auto-refresh de servicios...');
            refreshServices();
        }
    }, CONFIG.REFRESH_INTERVAL);
}

// ==================== INICIALIZACIÓN ====================

document.addEventListener('DOMContentLoaded', function() {
    console.log('📱 Inicializando dashboard...');
    
    // Auto-login si hay token guardado
    const savedToken = localStorage.getItem('roble_token');
    const savedUser = localStorage.getItem('roble_user');
    
    if (savedToken && savedUser) {
        console.log('🔑 Token encontrado, iniciando sesión automática...');
        currentToken = savedToken;
        currentUser = savedUser;
        showDashboard();
    }
    
    // Event listeners para formularios
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('create-service-form').addEventListener('submit', handleCreateService);
    
    // Event listeners para teclas
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
        if (e.key === 'Enter' && e.target.id === 'password') {
            handleLogin(e);
        }
    });
    
    // Event listener para test service change
    document.getElementById('test-service').addEventListener('change', updateTestEndpoint);
    
    console.log('✅ Dashboard inicializado correctamente');
});

// ==================== MANEJO DE ERRORES GLOBALES ====================

window.addEventListener('error', function(e) {
    console.error('❌ Error global capturado:', e.error);
    console.error('❌ Archivo:', e.filename);
    console.error('❌ Línea:', e.lineno);
    console.error('❌ Columna:', e.colno);
    console.error('❌ Stack trace completo:', e.error?.stack);
    
    // Si el error contiene "serviceName", mostrar información específica
    if (e.error?.message?.includes('serviceName')) {
        console.error('🔍 ERROR ESPECÍFICO DE serviceName detectado!');
        console.error('🔍 pendingAction actual:', pendingAction);
        console.error('🔍 activeServices:', activeServices);
    }
    
    showError('Ha ocurrido un error inesperado: ' + (e.error?.message || 'Error desconocido'));
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('❌ Promise rechazado:', e.reason);
    console.error('❌ Stack trace:', e.reason?.stack);
    
    if (e.reason?.message?.includes('serviceName')) {
        console.error('🔍 PROMISE REJECTION con serviceName detectado!');
        console.error('🔍 pendingAction actual:', pendingAction);
    }
    
    showError('Error de conexión con el servidor: ' + (e.reason?.message || 'Error desconocido'));
});

// ==================== UTILIDADES ADICIONALES ====================

// Función para validar JSON
function isValidJSON(str) {
    try {
        JSON.parse(str);
        return true;
    } catch (e) {
        return false;
    }
}

// Función para formatear fechas
function formatDate(dateString) {
    return new Date(dateString).toLocaleString('es-CO', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

console.log('🎉 Dashboard ROBLE completamente cargado y listo para usar');
