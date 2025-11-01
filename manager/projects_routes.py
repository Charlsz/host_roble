"""
Endpoints de Proyectos para la plataforma de Hosting
Gestión de proyectos web de usuarios
"""
from flask import Blueprint, request, jsonify
import logging
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

from roble_client import RobleClient
from deploy_service import DeployService
import docker

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')
logger = logging.getLogger(__name__)

# Instancia del cliente ROBLE
roble = RobleClient()

# Servicios de Docker y deploy
try:
    docker_client = docker.from_env()
    deploy_service = DeployService(docker_client)
    logger.info("Deploy service inicializado")
except Exception as e:
    logger.error(f"Error inicializando deploy service: {e}")
    docker_client = None
    deploy_service = None

def get_token_from_header():
    """Extrae el token del header Authorization"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    return auth_header.split(' ')[1]

def get_user_id_from_token(access_token):
    """Obtiene el user_id desde el token"""
    try:
        # Verificar token (esto devuelve la info del usuario)
        user_info = roble.verify_token(access_token)
        
        logger.info(f"🔍 Respuesta completa de verify_token: {user_info}")
        
        if not user_info:
            logger.error("verify_token retornó None")
            return None
        
        # Intentar diferentes campos posibles
        user_id = (user_info.get('uid') or 
                   user_info.get('email') or 
                   user_info.get('userId') or
                   user_info.get('user', {}).get('uid') or
                   user_info.get('user', {}).get('email'))
        
        if not user_id:
            logger.error(f"❌ No se pudo extraer user_id. Campos disponibles: {list(user_info.keys())}")
            return None
            
        logger.info(f"✅ User ID obtenido: {user_id}")
        return user_id
    except Exception as e:
        logger.error(f"❌ Error obteniendo user_id: {e}")
        return None

@projects_bp.route('/', methods=['GET'])
def get_projects():
    """
    Obtiene todos los proyectos del usuario autenticado
    
    Headers:
        Authorization: Bearer {accessToken}
        
    Returns:
        Lista de proyectos del usuario
    """
    try:
        access_token = get_token_from_header()
        if not access_token:
            return jsonify({'error': 'Token no proporcionado'}), 401
        
        user_id = get_user_id_from_token(access_token)
        if not user_id:
            return jsonify({'error': 'Usuario no válido'}), 401
        
        # Obtener proyectos del usuario
        projects = roble.get_user_projects(user_id, access_token)
        
        # Filtrar proyectos eliminados (status="deleted")
        active_projects = [p for p in projects if p.get('status') != 'deleted']
        
        print(f"\n====== DEBUG GET_PROJECTS ======", flush=True)
        print(f"Total proyectos activos: {len(active_projects)}", flush=True)
        for p in active_projects:
            print(f"Proyecto: {p.get('nombre')}, container_id: {p.get('container_id')}, status: {p.get('status')}", flush=True)
        print(f"================================\n", flush=True)
        
        # Agregar info de containers a cada proyecto con estado REAL de Docker
        docker_client = docker.from_env()
        for project in active_projects:
            container_id = project.get('container_id')
            
            # Si no hay container_id, buscar contenedor huérfano por nombre
            if not container_id:
                try:
                    # Construir nombre esperado del contenedor
                    expected_name = f"project_{user_id.replace('@', '_').replace('.', '_')}_{project.get('nombre')}"
                    containers = docker_client.containers.list(all=True, filters={"name": expected_name})
                    if containers:
                        container = containers[0]
                        container_id = container.id
                        project['container_id'] = container_id
                        logger.info(f"Contenedor huérfano encontrado y asociado: {container.name} -> {project.get('nombre')}")
                except Exception as e:
                    logger.error(f"Error buscando contenedor huérfano: {e}")
            
            if container_id:
                try:
                    # Obtener estado real del contenedor desde Docker
                    container = docker_client.containers.get(container_id)
                    project['real_status'] = container.status  # running, exited, etc.
                    
                    # Obtener puerto externo si está corriendo
                    if container.status == 'running':
                        ports = container.ports
                        # Buscar el puerto mapeado (80/tcp, 8080/tcp, etc.)
                        external_port = None
                        for internal, mappings in ports.items():
                            if mappings:
                                external_port = mappings[0]['HostPort']
                                break
                        project['external_port'] = external_port
                        project['url'] = f"http://localhost:{external_port}" if external_port else None
                    else:
                        project['external_port'] = None
                        project['url'] = None
                        
                except docker.errors.NotFound:
                    # El contenedor no existe en Docker
                    project['real_status'] = 'not_found'
                    project['external_port'] = None
                    project['url'] = None
                except Exception as e:
                    logger.error(f"Error obteniendo info de contenedor {container_id}: {e}")
                    project['real_status'] = 'error'
                    project['external_port'] = None
                    project['url'] = None
            else:
                project['real_status'] = project.get('status', 'pending')
                project['external_port'] = None
                project['url'] = None
        
        return jsonify({
            'success': True,
            'projects': active_projects
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener proyectos: {e}")
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/', methods=['POST'])
def create_project():
    """
    Crea un nuevo proyecto
    
    Headers:
        Authorization: Bearer {accessToken}
        
    Body:
        nombre: Nombre del proyecto (sin espacios, lowercase)
        repo_url: URL del repositorio GitHub
        
    Returns:
        Proyecto creado
    """
    try:
        access_token = get_token_from_header()
        if not access_token:
            return jsonify({'error': 'Token no proporcionado'}), 401
        
        user_id = get_user_id_from_token(access_token)
        if not user_id:
            return jsonify({'error': 'Usuario no válido'}), 401
        
        data = request.get_json()
        nombre = data.get('nombre')
        repo_url = data.get('repo_url')
        
        if not nombre or not repo_url:
            return jsonify({'error': 'Nombre y repo_url son requeridos'}), 400
        
        # Validar formato del nombre (sin espacios, lowercase)
        if ' ' in nombre or nombre != nombre.lower():
            return jsonify({'error': 'El nombre debe ser lowercase sin espacios'}), 400
        
        # Crear proyecto en ROBLE con estado 'pending'
        project = roble.create_project(user_id, nombre, repo_url, access_token)
        project_id = project.get('_id')
        
        logger.info(f"✅ Proyecto creado: {nombre} para usuario {user_id}")
        
        # Iniciar deploy en background
        if deploy_service:
            def deploy_callback(proj_id, status, message):
                """Callback para actualizar estado en ROBLE"""
                # TODO: Fix update_record para soportar actualizaciones
                logger.info(f"📊 Proyecto {proj_id}: {status} - {message}")
            
            def deploy_in_background():
                result = deploy_service.deploy_project(
                    project_id, nombre, user_id, repo_url, deploy_callback
                )
                
                # Actualizar con resultado final
                if result['success']:
                    try:
                        # Crear registro en tabla containers
                        container_data = {
                            'project_id': project_id,
                            'port': result['port'],
                            'status': 'running',
                            'cpu_limit': '0.5',
                            'memory_limit': '256m',
                            'image_name': result['image_name']
                        }
                        roble.insert_records('containers', [container_data], access_token)
                        logger.info(f"✅ Deploy completado: {nombre} en puerto {result['port']}")
                    except Exception as e:
                        logger.error(f"Error guardando container info: {e}")
                else:
                    logger.error(f"❌ Deploy falló: {result['message']}")
            
            import threading
            thread = threading.Thread(target=deploy_in_background)
            thread.daemon = True
            thread.start()
        
        return jsonify({
            'success': True,
            'project': project,
            'message': 'Proyecto creado. El despliegue iniciará automáticamente.'
        }), 201
        
    except Exception as e:
        logger.error(f"Error al crear proyecto: {e}")
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    """
    Obtiene información detallada de un proyecto
    
    Headers:
        Authorization: Bearer {accessToken}
        
    Returns:
        Información del proyecto y su contenedor
    """
    try:
        access_token = get_token_from_header()
        if not access_token:
            return jsonify({'error': 'Token no proporcionado'}), 401
        
        # Obtener proyecto
        projects = roble.read_records('proyectos', {'_id': project_id}, access_token)
        if not projects:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
        
        project = projects[0]
        
        # Obtener información del contenedor si existe
        container_info = None
        if project.get('container_id'):
            containers = roble.read_records('containers', {'project_id': project_id}, access_token)
            if containers:
                container_info = containers[0]
        
        return jsonify({
            'success': True,
            'project': project,
            'container': container_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener proyecto: {e}")
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    Elimina un proyecto y su contenedor asociado
    
    Headers:
        Authorization: Bearer {accessToken}
        
    Returns:
        Confirmación de eliminación
    """
    try:
        access_token = get_token_from_header()
        if not access_token:
            return jsonify({'error': 'Token no proporcionado'}), 401
        
        user_id = get_user_id_from_token(access_token)
        
        # Verificar que el proyecto pertenece al usuario
        projects = roble.read_records('proyectos', {'_id': project_id}, access_token)
        if not projects:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
        
        project = projects[0]
        if project.get('user_id') != user_id:
            return jsonify({'error': 'No tienes permiso para eliminar este proyecto'}), 403
        
        # Detener y eliminar contenedor Docker
        if project.get('container_id') and deploy_service:
            success, message = deploy_service.remove_container(project['container_id'])
            if not success:
                logger.warning(f"Error eliminando contenedor: {message}")
        
        # TEMPORALMENTE: Solo limpiamos Docker, no ROBLE DB
        # Buscar contenedor por nombre y eliminarlo
        nombre = project.get('nombre')
        if nombre and deploy_service:
            try:
                container_name = f"project_{user_id}_{nombre}".lower().replace('@', '_').replace('.', '_')
                containers = deploy_service.docker_client.containers.list(all=True, filters={"name": container_name})
                for container in containers:
                    container.remove(force=True)
                    logger.info(f"✅ Contenedor eliminado: {container_name}")
            except Exception as e:
                logger.warning(f"Error limpiando contenedores: {e}")
        
        # Intentar eliminar/marcar como deleted en ROBLE
        try:
            # Opción 1: Intentar DELETE directo
            roble.delete_record('proyectos', '_id', project_id, access_token)
            logger.info(f"✅ Proyecto eliminado completamente de ROBLE: {project_id}")
        except Exception as roble_error:
            # Opción 2: Si falla DELETE, intentar UPDATE a status="deleted"
            try:
                updates = {'status': 'deleted'}
                roble.update_record('proyectos', '_id', project_id, updates, access_token)
                logger.info(f"✅ Proyecto marcado como deleted en ROBLE: {project_id}")
            except Exception as update_error:
                logger.warning(f"⚠️ No se pudo eliminar/marcar en ROBLE: {update_error}")
        
        logger.info(f"✅ Proyecto limpiado: {project_id}")
        return jsonify({'message': 'Proyecto eliminado'}), 200
        
    except Exception as e:
        logger.error(f"Error al eliminar proyecto: {e}")
        return jsonify({'error': str(e)}), 500

@projects_bp.route('/<project_id>/rebuild', methods=['POST'])
def rebuild_project(project_id):
    """
    Reconstruye un proyecto desde GitHub
    
    Headers:
        Authorization: Bearer {accessToken}
        
    Returns:
        Confirmación de reconstrucción iniciada
    """
    try:
        access_token = get_token_from_header()
        if not access_token:
            return jsonify({'error': 'Token no proporcionado'}), 401
        
        user_id = get_user_id_from_token(access_token)
        
        # Verificar que el proyecto pertenece al usuario
        projects = roble.read_records('proyectos', {'_id': project_id}, access_token)
        if not projects:
            return jsonify({'error': 'Proyecto no encontrado'}), 404
        
        project = projects[0]
        if project.get('user_id') != user_id:
            return jsonify({'error': 'No tienes permiso para reconstruir este proyecto'}), 403
        
        # Actualizar estado a building
        roble.update_project_status(project_id, 'building', access_token=access_token)
        
        # Detener contenedor anterior si existe
        if project.get('container_id') and deploy_service:
            deploy_service.remove_container(project['container_id'])
        
        # Rebuild en background
        if deploy_service:
            def rebuild_callback(proj_id, status, message):
                """Callback para actualizar estado"""
                try:
                    roble.update_project_status(proj_id, status, access_token)
                    logger.info(f"Rebuild {proj_id}: {status} - {message}")
                except Exception as e:
                    logger.error(f"Error actualizando estado: {e}")
            
            def rebuild_in_background():
                result = deploy_service.deploy_project(
                    project_id, 
                    project['nombre'], 
                    user_id, 
                    project['repo_url'], 
                    rebuild_callback
                )
                
                if result['success']:
                    # Actualizar container info
                    roble.update_record(
                        'containers',
                        {'project_id': project_id},
                        {
                            'port': result['port'],
                            'status': 'running',
                            'image_name': result['image_name']
                        },
                        access_token
                    )
                    
                    roble.update_record(
                        'proyectos',
                        project_id,
                        {'container_id': result['container_id']},
                        access_token
                    )
                    logger.info(f"✅ Rebuild completado: {project['nombre']}")
                else:
                    roble.update_project_status(project_id, 'error', access_token)
                    logger.error(f"❌ Rebuild falló: {result['message']}")
            
            import threading
            thread = threading.Thread(target=rebuild_in_background)
            thread.daemon = True
            thread.start()
        
        logger.info(f"✅ Rebuild iniciado para proyecto: {project_id}")
        
        return jsonify({
            'success': True,
            'message': 'Reconstrucción iniciada'
        }), 200
        
    except Exception as e:
        logger.error(f"Error al reconstruir proyecto: {e}")
        return jsonify({'error': str(e)}), 500
