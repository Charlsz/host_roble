"""
Manager de Microservicios ROBLE - Plataforma de Hosting
Gestiona microservicios y proyectos web con Docker SDK
"""
import os
import logging
import requests
import docker
import tempfile
import shutil
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json

# Importar blueprints de autenticación y proyectos
from auth_routes import auth_bp
from projects_routes import projects_bp
from activity_monitor import ActivityMonitor

# Configuración
app = Flask(__name__)
CORS(app, origins=["http://localhost:8080", "http://127.0.0.1:8080"], 
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Registrar blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(projects_bp)
logger.info("✅ Blueprints de autenticación y proyectos registrados")

# Variables de entorno ROBLE
ROBLE_BASE_HOST = os.getenv('ROBLE_BASE_HOST', 'https://roble-api.openlab.uninorte.edu.co')
ROBLE_CONTRACT = os.getenv('ROBLE_CONTRACT', 'microservices_roble_e65ac352d7')

# Cliente Docker
try:
    docker_client = docker.from_env()
    logger.info("✅ Cliente Docker conectado")
except Exception as e:
    logger.error(f"❌ Error conectando con Docker: {e}")
    docker_client = None

# Inicializar monitor de actividad (30 minutos = 1800 segundos)
activity_monitor = None
if docker_client:
    activity_monitor = ActivityMonitor(docker_client, inactivity_timeout=1800)
    activity_monitor.start_monitoring()
    logger.info("✅ Monitor de actividad iniciado (timeout: 30 minutos)")

def get_activity_monitor():
    """Obtiene la instancia del monitor de actividad"""
    return activity_monitor


def cleanup_dynamic_containers():
    """Limpia contenedores dinámicos al inicio para evitar conflictos de puertos"""
    logger.info("🧹 Iniciando limpieza de contenedores dinámicos...")
    
    if not docker_client:
        logger.warning("Docker no disponible para limpieza")
        return
    
    try:
        # Buscar todos los contenedores y filtrar por nombre que contenga 'dynamic_'
        all_containers = docker_client.containers.list(all=True)
        containers = [c for c in all_containers if 'dynamic_' in c.name]
        
        logger.info(f"🔍 Encontrados {len(containers)} contenedores dinámicos")
        
        if containers:
            logger.info(f"🧹 Limpiando {len(containers)} contenedores dinámicos existentes...")
            
            for container in containers:
                try:
                    # Detener si está corriendo
                    if container.status == 'running':
                        container.stop()
                        logger.info(f"⏹️ Detenido: {container.name}")
                    
                    # Eliminar el contenedor
                    container.remove()
                    logger.info(f"🗑️ Eliminado: {container.name}")
                    
                except Exception as e:
                    logger.warning(f"Error eliminando contenedor {container.name}: {e}")
            
            # Limpiar imágenes de microservicios también
            try:
                images = docker_client.images.list(filters={"reference": "microservice_*"})
                for image in images:
                    try:
                        docker_client.images.remove(image.id, force=True)
                        logger.info(f"🗑️ Imagen eliminada: {image.tags}")
                    except Exception as e:
                        logger.warning(f"Error eliminando imagen {image.id}: {e}")
            except Exception as e:
                logger.warning(f"Error limpiando imágenes: {e}")
                
            logger.info("✅ Limpieza de contenedores dinámicos completada")
        else:
            logger.info("✨ No hay contenedores dinámicos para limpiar")
            
    except Exception as e:
        logger.error(f"❌ Error durante la limpieza: {e}")

# Ejecutar limpieza al iniciar
# (Esta función se ejecutará en el bloque main)

# Registro de microservicios disponibles (dinámico + estáticos)
available_microservices = {
    'filter-service': {
        'id': 'filter-001',
        'name': 'filter-service',
        'type': 'filter',
        'container_name': 'filter_service',
        'port': 5001,
        'endpoint': 'http://filter-service:5000',
        'internal_endpoint': 'http://filter-service:5000',
        'status': 'running',
        'created_at': datetime.now().isoformat(),
        'config': {'description': 'Servicio de filtrado de usuarios ROBLE'},
        'is_static': True
    },
    'aggregate-service': {
        'id': 'aggregate-001', 
        'name': 'aggregate-service',
        'type': 'aggregate',
        'container_name': 'aggregate_service',
        'port': 5002,
        'endpoint': 'http://aggregate-service:5000',
        'internal_endpoint': 'http://aggregate-service:5000',
        'status': 'running',
        'created_at': datetime.now().isoformat(),
        'config': {'description': 'Servicio de agregación de datos ROBLE'},
        'is_static': True
    }
}

# Contador para puertos dinámicos
next_available_port = 5003

current_user_token = None

# --- FUNCIONES ROBLE ---
def roble_login(email, password):
    """Login en ROBLE"""
    try:
        url = f"{ROBLE_BASE_HOST}/auth/{ROBLE_CONTRACT}/login"
        logger.info(f"Intentando login con URL: {url}")
        logger.info(f"Email: {email}")
        
        payload = {"email": email, "password": password}
        response = requests.post(url, json=payload, timeout=10)
        
        logger.info(f"Status de respuesta: {response.status_code}")
        logger.info(f"Respuesta: {response.text[:200]}...")
        
        # ROBLE devuelve 201 (Created) en lugar de 200 para login exitoso
        if response.status_code in [200, 201]:
            data = response.json()
            # El token viene en 'accessToken', no en 'token'
            if 'accessToken' in data:
                data['token'] = data['accessToken']  # Normalizar el nombre
            return data
        else:
            logger.error(f"Login falló - Status: {response.status_code}, Response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error de conexión en login ROBLE: {e}")
        return None

def roble_verify_token(token):
    """Verificar token en ROBLE"""
    try:
        url = f"{ROBLE_BASE_HOST}/auth/{ROBLE_CONTRACT}/verify-token"
        response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        return response.status_code == 200
    except:
        return False

def roble_check_permissions(token, action='read'):
    """Verificar permisos específicos del usuario"""
    try:
        url = f"{ROBLE_BASE_HOST}/auth/{ROBLE_CONTRACT}/verify-token"
        response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        
        if response.status_code == 200:
            user_data = response.json()
            
            # Debug: mostrar toda la respuesta
            logger.info(f"Respuesta completa del token: {user_data}")
            
            # Extraer información del usuario correctamente según la estructura de ROBLE
            user_info = user_data.get('user', {})
            user_role = user_info.get('role', 'user')  # El rol está dentro de 'user'
            user_email = user_info.get('email', '')   # El email está dentro de 'user'
            
            # Log para debugging
            logger.info(f"Usuario verificado: {user_email}, Rol: {user_role}")
            
            # Lógica de permisos más permisiva para admins
            if action in ['create', 'delete']:
                # Permitir si es admin O si el email contiene @uninorte.edu.co (admin de facto)
                if user_role == 'admin' or '@uninorte.edu.co' in user_email:
                    logger.info(f"Permisos concedidos para {user_email} (rol: {user_role})")
                    return True
                logger.warning(f"Permisos insuficientes para {user_email} (rol: {user_role})")
                return False
            return True
        else:
            logger.error(f"Error verificando token: {response.status_code}")
        return False
    except Exception as e:
        logger.error(f"Error en verificación de permisos: {e}")
        return False

def check_user_permissions(token, action):
    """Helper para verificar permisos y retornar respuesta adecuada"""
    if not token or not roble_verify_token(token):
        return jsonify({"error": "Token inválido o expirado"}), 401
    
    if not roble_check_permissions(token, action):
        return jsonify({"error": "Permisos insuficientes para esta acción"}), 403
    
    return None

# --- GESTIÓN DE MICROSERVICIOS (DOCKER REAL) ---
def check_service_health(service_info):
    """Verifica si un microservicio está funcionando"""
    try:
        response = requests.get(f"{service_info['internal_endpoint']}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def create_microservice_files(service_name, service_type, custom_code=None):
    """Crea archivos temporales para el microservicio"""
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Template Dockerfile inline
        dockerfile_content = """FROM python:3.9-slim

WORKDIR /app

RUN pip install flask requests flask-cors

COPY app.py .

EXPOSE 5000

CMD ["python", "app.py"]
"""
        
        with open(os.path.join(temp_dir, 'Dockerfile'), 'w') as f:
            f.write(dockerfile_content)
        
        # Usar código personalizado si se proporciona, sino usar plantilla
        if custom_code:
            app_content = custom_code
            logger.info(f"📝 Usando código personalizado para {service_name} ({len(custom_code)} caracteres)")
        else:
            # Template app.py inline por defecto
            app_content = f"""\"\"\"
Microservicio {service_name} - Tipo: {service_type}
Generado automáticamente por el Manager ROBLE
\"\"\"
import os
import logging
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración ROBLE
ROBLE_BASE_HOST = os.getenv('ROBLE_BASE_HOST', 'https://roble-api.openlab.uninorte.edu.co')
ROBLE_CONTRACT = os.getenv('ROBLE_CONTRACT', 'microservices_roble_e65ac352d7')

@app.route('/health')
def health():
    return jsonify({{"status": "running", "service": "{service_name}", "type": "{service_type}"}})

@app.route('/process', methods=['POST'])
def process_data():
    try:
        data = request.get_json() or {{}}
        
        # Lógica específica por tipo
        if "{service_type}" == "filter":
            result = {{"filtered_data": data, "service": "{service_name}", "processed": True}}
        elif "{service_type}" == "aggregate":
            result = {{"aggregated_data": data, "service": "{service_name}", "count": len(str(data))}}
        else:
            result = {{"processed_data": data, "service": "{service_name}", "type": "{service_type}"}}
        
        return jsonify(result)
    except Exception as e:
        return jsonify({{"error": str(e)}}), 500

# Endpoint específico para filter
@app.route('/filter', methods=['POST'])
def filter_data():
    try:
        data = request.get_json() or {{}}
        result = {{"filtered_data": data, "service": "{service_name}", "processed": True}}
        return jsonify(result)
    except Exception as e:
        return jsonify({{"error": str(e)}}), 500

# Endpoint específico para aggregate
@app.route('/aggregate', methods=['POST'])
def aggregate_data():
    try:
        data = request.get_json() or {{}}
        result = {{"aggregated_data": data, "service": "{service_name}", "count": len(str(data))}}
        return jsonify(result)
    except Exception as e:
        return jsonify({{"error": str(e)}}), 500

if __name__ == '__main__':
    logger.info(f"🚀 Iniciando {service_name} ({service_type})")
    app.run(host='0.0.0.0', port=5000, debug=True)
"""
        
        with open(os.path.join(temp_dir, 'app.py'), 'w') as f:
            f.write(app_content)
        
        return temp_dir
    except Exception as e:
        logger.error(f"Error creando archivos para microservicio: {e}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None

def find_available_port(start_port=5003):
    """Encuentra un puerto disponible comenzando desde start_port"""
    import socket
    import time
    import random
    
    # Agregar un poco de randomness para evitar colisiones
    start_port += random.randint(0, 10)
    
    for port in range(start_port, start_port + 100):  # Buscar en un rango de 100 puertos
        try:
            # Verificar si el puerto está libre en el host
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue
    
    # Si no encuentra ningún puerto libre, usar uno aleatorio alto
    return random.randint(6000, 7999)

def create_real_microservice(service_type, service_name, config=None, custom_code=None):
    """Crea un microservicio Docker real"""
    global next_available_port
    
    if not docker_client:
        logger.error("Docker no disponible")
        return None

    try:
        # Crear archivos del microservicio (con código personalizado si se proporciona)
        temp_dir = create_microservice_files(service_name, service_type, custom_code)
        if not temp_dir:
            return None        # Encontrar puerto disponible
        available_port = find_available_port(next_available_port)
        
        # Actualizar el siguiente puerto disponible
        next_available_port = available_port + 1
        
        # Generar nombre único del contenedor con timestamp más preciso y UUID corto
        import uuid
        import time
        # Usar tiempo en microsegundos para mayor unicidad
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S') + f"_{int(time.time() * 1000000) % 1000000}"
        unique_id = str(uuid.uuid4())[:8]  # 8 caracteres únicos
        container_name = f"dynamic_{service_name}_{timestamp}_{unique_id}"
        image_name = f"microservice_{service_name.lower()}:latest"
        
        # Construir imagen Docker
        logger.info(f"Construyendo imagen {image_name}...")
        image, build_logs = docker_client.images.build(
            path=temp_dir,
            tag=image_name,
            rm=True
        )
        
        # Crear y ejecutar contenedor
        logger.info(f"Creando contenedor {container_name} en puerto {available_port}...")
        container = docker_client.containers.run(
            image_name,
            name=container_name,
            ports={'5000/tcp': available_port},
            environment={
                'ROBLE_BASE_HOST': ROBLE_BASE_HOST,
                'ROBLE_CONTRACT': ROBLE_CONTRACT,
                'SERVICE_NAME': service_name
            },
            network='microservices_roble_microservices_network',
            detach=True
        )
        
        # Crear registro del microservicio
        service_info = {
            'id': f"{service_type}-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'name': service_name,
            'type': service_type,
            'container_name': container_name,
            'container_id': container.id,
            'image_name': image_name,
            'port': available_port,
            'endpoint': f"http://{container_name}:5000",
            'internal_endpoint': f"http://{container_name}:5000",
            'external_endpoint': f"http://localhost:{available_port}",
            'status': 'running',
            'created_at': datetime.now().isoformat(),
            'config': config or {},
            'is_static': False,
            'temp_dir': temp_dir
        }
        
        # Añadir al registro
        available_microservices[service_name] = service_info
        
        logger.info(f"✅ Microservicio {service_name} creado exitosamente en puerto {available_port}")
        return service_info
        
    except Exception as e:
        logger.error(f"Error creando microservicio {service_name}: {e}")
        if 'temp_dir' in locals() and temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
        return None

def delete_real_microservice(service_id):
    """Elimina un microservicio Docker real"""
    if not docker_client:
        return False
    
    try:
        # Buscar el microservicio
        service_info = None
        service_key = None
        
        for key, info in available_microservices.items():
            if info['id'] == service_id or info['name'] == service_id:
                service_info = info
                service_key = key
                break
        
        if not service_info:
            logger.error(f"Microservicio {service_id} no encontrado")
            return False
        
        # No eliminar servicios estáticos
        if service_info.get('is_static', False):
            logger.warning(f"No se puede eliminar el microservicio estático {service_id}")
            return False
        
        # Detener y eliminar contenedor
        if 'container_id' in service_info:
            try:
                container = docker_client.containers.get(service_info['container_id'])
                container.stop()
                container.remove()
                logger.info(f"Contenedor {service_info['container_name']} eliminado")
            except Exception as e:
                logger.warning(f"Error eliminando contenedor: {e}")
        
        # Eliminar imagen
        if 'image_name' in service_info:
            try:
                docker_client.images.remove(service_info['image_name'], force=True)
                logger.info(f"Imagen {service_info['image_name']} eliminada")
            except Exception as e:
                logger.warning(f"Error eliminando imagen: {e}")
        
        # Limpiar archivos temporales
        if 'temp_dir' in service_info:
            try:
                shutil.rmtree(service_info['temp_dir'], ignore_errors=True)
            except:
                pass
        
        # Eliminar del registro
        del available_microservices[service_key]
        logger.info(f"✅ Microservicio {service_id} eliminado exitosamente")
        
        return True
        
    except Exception as e:
        logger.error(f"Error eliminando microservicio {service_id}: {e}")
        return False

def create_virtual_microservice(service_type, service_name, config=None):
    """LEGACY: Simula la creación de un microservicio (para demo, usa los existentes)"""
    if service_type == 'filter':
        base_service = available_microservices['filter-service'].copy()
    elif service_type == 'aggregate':
        base_service = available_microservices['aggregate-service'].copy()
    else:
        return None
    
    # Personalizar el nuevo "microservicio"
    new_service = base_service.copy()
    new_service['id'] = f"{service_type}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    new_service['name'] = service_name
    new_service['config'] = config or {}
    new_service['created_at'] = datetime.now().isoformat()
    new_service['status'] = 'running' if check_service_health(new_service) else 'stopped'
    
    return new_service

# --- API ENDPOINTS ---
@app.route('/')
def api_info():
    """Información de la API"""
    return jsonify({
        "service": "Microservices Manager API",
        "version": "2.0", 
        "status": "running",
        "message": "API funcionando correctamente",
        "dashboard_url": "http://localhost:8080",
        "endpoints": {
            "status": "/api/status",
            "login": "/api/login",
            "microservices": "/api/microservices",
            "test_roble": "/api/test-roble"
        }
    })

@app.route('/api/status')
def api_status():
    """Estado del Manager"""
    return jsonify({
        "service": "Microservices Manager - Optimized",
        "version": "2.0",
        "status": "running",
        "endpoints": {
            "login": "/api/login",
            "microservices": "/api/microservices"
        },
        "available_services": list(available_microservices.keys())
    })

@app.route('/api/login', methods=['POST'])
def api_login():
    """Login con ROBLE"""
    global current_user_token
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email y password requeridos"}), 400
    
    result = roble_login(email, password)
    if result and 'token' in result:
        current_user_token = result['token']
        return jsonify({
            "success": True,
            "message": "Login exitoso",
            "token": result['token']
        })
    else:
        return jsonify({"error": "Credenciales inválidas"}), 401

@app.route('/api/test-roble', methods=['GET'])
def api_test_roble():
    """Endpoint de prueba para diagnosticar conexión con ROBLE"""
    try:
        # Probar conectividad básica
        base_url = ROBLE_BASE_HOST
        test_url = f"{base_url}/auth/{ROBLE_CONTRACT}/login"
        
        # Hacer una petición de prueba
        response = requests.post(test_url, json={"email": "test@test.com", "password": "test"}, timeout=5)
        
        return jsonify({
            "roble_host": ROBLE_BASE_HOST,
            "roble_contract": ROBLE_CONTRACT,
            "test_url": test_url,
            "response_status": response.status_code,
            "response_text": response.text[:300],
            "connection_ok": True
        })
    except Exception as e:
        return jsonify({
            "roble_host": ROBLE_BASE_HOST,
            "roble_contract": ROBLE_CONTRACT,
            "error": str(e),
            "connection_ok": False
        })

@app.route('/api/microservices', methods=['GET'])
def api_list_microservices():
    """Lista microservicios activos"""
    services = []
    for service_id, service_info in available_microservices.items():
        service_copy = service_info.copy()
        service_copy['status'] = 'running' if check_service_health(service_info) else 'stopped'
        service_copy['external_endpoint'] = f"http://localhost:{service_info['port']}"
        services.append(service_copy)
    
    return jsonify({
        "microservices": services,
        "total": len(services)
    })

@app.route('/api/microservices', methods=['POST'])
def api_create_microservice():
    """Crea un microservicio Docker real"""
    # Verificar permisos
    perm_check = check_user_permissions(current_user_token, 'create')
    if perm_check:
        return perm_check
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Datos JSON requeridos"}), 400
            
        service_type = data.get('type')
        service_name = data.get('name')
        config = data.get('config', {})
        custom_code = data.get('custom_code')  # Nuevo: código personalizado
        
        if not service_type or not service_name:
            return jsonify({"success": False, "error": "Tipo y nombre de servicio requeridos"}), 400
        
        if service_type not in ['filter', 'aggregate', 'custom']:
            return jsonify({"success": False, "error": "Tipo de servicio no válido. Use: filter, aggregate, custom"}), 400
        
        # Verificar que el nombre no exista
        if service_name in available_microservices:
            return jsonify({"success": False, "error": f"Ya existe un microservicio con el nombre '{service_name}'"}), 400
        
        # Log del código personalizado
        if custom_code:
            logger.info(f"📝 Código personalizado recibido para {service_name}: {len(custom_code)} caracteres")
        
        # Crear microservicio real (pasando código personalizado)
        service_info = create_real_microservice(service_type, service_name, config, custom_code)
        
        if service_info:
            return jsonify({
                "success": True,
                "message": f"Microservicio '{service_name}' creado exitosamente",
                "service": service_info,
                "container_id": service_info.get('container_id'),
                "external_url": service_info.get('external_endpoint'),
                "has_custom_code": bool(custom_code)
            }), 201
        else:
            return jsonify({"success": False, "error": "Error interno creando microservicio"}), 500
            
    except Exception as e:
        logger.error(f"Error en api_create_microservice: {e}")
        return jsonify({"success": False, "error": f"Error procesando solicitud: {str(e)}"}), 500

@app.route('/api/microservices/<service_id>', methods=['DELETE'])
def api_delete_microservice(service_id):
    """Elimina un microservicio Docker real"""
    # Verificar permisos
    perm_check = check_user_permissions(current_user_token, 'delete')
    if perm_check:
        return perm_check
    
    # Intentar eliminar microservicio
    success = delete_real_microservice(service_id)
    
    if success:
        return jsonify({
            "success": True,
            "message": f"Microservicio {service_id} eliminado exitosamente"
        })
    else:
        return jsonify({"error": "Error eliminando microservicio o microservicio no encontrado"}), 400

@app.route('/api/microservices/<service_id>', methods=['PUT'])
def api_edit_microservice(service_id):
    """Edita la configuración de un microservicio"""
    if not current_user_token or not roble_verify_token(current_user_token):
        return jsonify({"error": "Token inválido o expirado"}), 401
    
    # Buscar el microservicio
    service_info = None
    service_key = None
    
    for key, info in available_microservices.items():
        if info['id'] == service_id or info['name'] == service_id:
            service_info = info
            service_key = key
            break
    
    if not service_info:
        return jsonify({"error": "Microservicio no encontrado"}), 404
    
    if service_info.get('is_static', False):
        return jsonify({"error": "No se pueden editar microservicios estáticos"}), 403
    
    # Actualizar configuración
    data = request.get_json()
    if 'config' in data:
        service_info['config'].update(data['config'])
    
    return jsonify({
        "success": True,
        "message": f"Microservicio {service_id} editado exitosamente",
        "service": service_info
    })

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "available_microservices": len(available_microservices)
    })

@app.route('/api/cleanup', methods=['POST'])
def cleanup_containers():
    """Endpoint para limpiar contenedores dinámicos manualmente"""
    try:
        print("🧹 API: Iniciando limpieza manual de contenedores dinámicos...")
        
        if not docker_client:
            return jsonify({
                "success": False,
                "message": "Docker no disponible",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # Buscar contenedores dinámicos
        all_containers = docker_client.containers.list(all=True)
        containers = [c for c in all_containers if 'dynamic_' in c.name]
        
        cleaned_containers = []
        cleaned_images = []
        
        if containers:
            for container in containers:
                try:
                    container_name = container.name
                    # Detener si está corriendo
                    if container.status == 'running':
                        container.stop()
                        print(f"⏹️ API: Detenido: {container_name}")
                    
                    # Eliminar el contenedor
                    container.remove()
                    print(f"🗑️ API: Eliminado: {container_name}")
                    cleaned_containers.append(container_name)
                    
                except Exception as e:
                    print(f"❌ API: Error eliminando contenedor {container.name}: {e}")
            
            # Limpiar imágenes de microservicios también
            try:
                images = docker_client.images.list(filters={"reference": "microservice_*"})
                for image in images:
                    try:
                        image_id = image.id
                        docker_client.images.remove(image.id, force=True)
                        print(f"🗑️ API: Imagen eliminada: {image.tags}")
                        cleaned_images.append(image_id[:12])
                    except Exception as e:
                        print(f"❌ API: Error eliminando imagen {image.id}: {e}")
            except Exception as e:
                print(f"❌ API: Error limpiando imágenes: {e}")
        
        return jsonify({
            "success": True,
            "message": f"Limpieza completada: {len(cleaned_containers)} contenedores, {len(cleaned_images)} imágenes",
            "cleaned_containers": cleaned_containers,
            "cleaned_images": cleaned_images,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ API: Error durante la limpieza: {e}")
        return jsonify({
            "success": False,
            "message": f"Error durante la limpieza: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500



if __name__ == '__main__':
    print("🐛 DEBUG: Entrando al bloque __main__")
    print("🐛 DEBUG: __name__ =", __name__)
    
    try:
        print("🧹 EJECUTANDO LIMPIEZA AUTOMÁTICA DE CONTENEDORES DINÁMICOS...")
        cleanup_dynamic_containers()
        print("✅ LIMPIEZA AUTOMÁTICA COMPLETADA")
    except Exception as e:
        print(f"❌ ERROR EN LIMPIEZA AUTOMÁTICA: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)
    print("🚀 ROBLE MICROSERVICES PLATFORM")
    print("=" * 60)
    print(f"� Dashboard: http://localhost:8080")
    print(f"🔧 Manager API: http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False)