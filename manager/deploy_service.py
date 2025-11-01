"""
Servicio de despliegue de proyectos desde GitHub
Maneja clonación, build de imágenes Docker y deploy de contenedores
"""
import os
import logging
import tempfile
import shutil
import subprocess
import docker
import time
from typing import Dict, Optional, Tuple
import threading

logger = logging.getLogger(__name__)

class DeployService:
    """Servicio para desplegar proyectos desde GitHub"""
    
    def __init__(self, docker_client):
        self.docker_client = docker_client
        self.base_port = 7000  # Cambiado de 6000 a 7000 para evitar conflictos
        self.used_ports = set()
        self._load_used_ports()
    
    def _load_used_ports(self):
        """Carga los puertos ya en uso"""
        try:
            containers = self.docker_client.containers.list(all=True)
            for container in containers:
                if container.name.startswith('project_'):
                    for port_binding in container.attrs.get('NetworkSettings', {}).get('Ports', {}).values():
                        if port_binding:
                            for binding in port_binding:
                                self.used_ports.add(int(binding['HostPort']))
        except Exception as e:
            logger.error(f"Error cargando puertos: {e}")
    
    def _get_next_port(self) -> int:
        """Obtiene el siguiente puerto disponible"""
        port = self.base_port
        while port in self.used_ports or port > 7999:  # Rango 7000-7999
            port += 1
        self.used_ports.add(port)
        return port
    
    def clone_repository(self, repo_url: str, temp_dir: str) -> Tuple[bool, str]:
        """
        Clona un repositorio de GitHub
        
        Returns:
            (success, message)
        """
        try:
            logger.info(f"Clonando repositorio: {repo_url}")
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', repo_url, temp_dir],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(f"Repositorio clonado exitosamente")
                return True, "Repositorio clonado"
            else:
                error_msg = result.stderr or result.stdout
                logger.error(f"Error clonando repo: {error_msg}")
                return False, f"Error al clonar: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout al clonar repositorio"
        except Exception as e:
            logger.error(f"Excepción clonando repo: {e}")
            return False, str(e)
    
    def build_image(self, project_name: str, user_id: str, temp_dir: str) -> Tuple[bool, str, Optional[str]]:
        """
        Construye una imagen Docker desde el repositorio
        
        Returns:
            (success, message, image_name)
        """
        try:
            # Verificar que existe Dockerfile
            dockerfile_path = os.path.join(temp_dir, 'Dockerfile')
            if not os.path.exists(dockerfile_path):
                return False, "No se encontró Dockerfile en el repositorio", None
            
            # Nombre de la imagen
            image_name = f"project_{user_id}_{project_name}:latest".lower().replace('@', '_').replace('.', '_')
            
            logger.info(f"Construyendo imagen: {image_name}")
            
            # Build con Docker SDK
            image, build_logs = self.docker_client.images.build(
                path=temp_dir,
                tag=image_name,
                rm=True,
                forcerm=True
            )
            
            logger.info(f"Imagen construida exitosamente: {image_name}")
            return True, "Imagen construida", image_name
            
        except docker.errors.BuildError as e:
            error_msg = str(e)
            logger.error(f"Error construyendo imagen: {error_msg}")
            return False, f"Error en build: {error_msg}", None
        except Exception as e:
            logger.error(f"Excepción construyendo imagen: {e}")
            return False, str(e), None
    
    def deploy_container(self, project_id: str, project_name: str, user_id: str, 
                        image_name: str) -> Tuple[bool, str, Optional[int], Optional[str]]:
        """
        Despliega un contenedor desde la imagen con retry en caso de puerto ocupado
        
        Returns:
            (success, message, port, container_id)
        """
        max_retries = 10  # Intentar hasta 10 puertos diferentes
        
        for attempt in range(max_retries):
            try:
                # Asignar puerto
                port = self._get_next_port()
                
                # Nombre del contenedor
                container_name = f"project_{user_id}_{project_name}".lower().replace('@', '_').replace('.', '_')
                
                logger.info(f"Desplegando contenedor: {container_name} en puerto {port} (intento {attempt + 1})")
                
                # Mapear un solo puerto interno al puerto externo
                # Orden: 80 (nginx), 8080, 3000 (node), 5000 (flask), 8000
                internal_ports = ['80/tcp', '8080/tcp', '3000/tcp', '5000/tcp', '8000/tcp']
                
                # Solo mapeamos el primer puerto (más común es 80 para nginx/apache)
                port_bindings = {internal_ports[0]: port}
                
                # Crear e iniciar contenedor
                container = self.docker_client.containers.run(
                    image_name,
                    name=container_name,
                    detach=True,
                    ports=port_bindings,
                    restart_policy={"Name": "no"},
                    mem_limit="256m",
                    cpu_quota=50000,  # 0.5 CPU
                    labels={
                        "project_id": project_id,
                        "user_id": user_id,
                        "project_name": project_name
                    }
                )
                
                logger.info(f"✅ Contenedor desplegado y corriendo: {container.id[:12]} en puerto {port}")
                return True, "Contenedor desplegado", port, container.id
                
            except Exception as container_error:
                error_str = str(container_error).lower()
                
                # Detectar errores de puerto ocupado (múltiples variantes)
                port_errors = [
                    "port is already allocated",
                    "address already in use", 
                    "bind: only one usage of each socket address",
                    "ports are not available",
                    "listen tcp"
                ]
                
                is_port_error = any(err in error_str for err in port_errors)
                
                if is_port_error:
                    logger.warning(f"⚠️ Puerto {port} ocupado, reintentando con siguiente puerto...")
                    
                    # Limpiar contenedor zombie si se creó
                    try:
                        zombie_containers = self.docker_client.containers.list(
                            all=True, 
                            filters={"name": container_name}
                        )
                        for zombie in zombie_containers:
                            logger.warning(f"🧹 Limpiando contenedor zombie: {zombie.name}")
                            zombie.remove(force=True)
                    except Exception as cleanup_error:
                        logger.warning(f"Error limpiando zombie: {cleanup_error}")
                    
                    # Esperar un poco antes de reintentar (ayuda con puertos fantasma en Windows)
                    time.sleep(0.5)
                    
                    # Continuar con siguiente intento
                    continue
                else:
                    # Error diferente, no reintentar
                    logger.error(f"❌ Error fatal al crear/iniciar contenedor: {container_error}")
                    
                    # Intentar limpiar si quedó zombie
                    try:
                        zombie_containers = self.docker_client.containers.list(
                            all=True, 
                            filters={"name": container_name}
                        )
                        for zombie in zombie_containers:
                            zombie.remove(force=True)
                    except:
                        pass
                    
                    return False, str(container_error), None, None
        
        # Si llegamos aquí, fallaron todos los intentos
        logger.error(f"❌ No se pudo desplegar después de {max_retries} intentos")
        return False, f"No hay puertos disponibles después de {max_retries} intentos", None, None
    
    def deploy_project(self, project_id: str, project_name: str, user_id: str, 
                      repo_url: str, callback=None) -> Dict:
        """
        Proceso completo de despliegue (clone -> build -> deploy)
        
        Args:
            callback: Función para reportar progreso (opcional)
        """
        result = {
            'success': False,
            'message': '',
            'port': None,
            'container_id': None,
            'image_name': None
        }
        
        temp_dir = None
        
        try:
            # 1. Crear directorio temporal
            temp_dir = tempfile.mkdtemp(prefix=f"project_{project_name}_")
            
            if callback:
                callback(project_id, 'building', 'Clonando repositorio...')
            
            # 2. Clonar repositorio
            success, message = self.clone_repository(repo_url, temp_dir)
            if not success:
                result['message'] = message
                return result
            
            if callback:
                callback(project_id, 'building', 'Construyendo imagen Docker...')
            
            # 3. Build imagen
            success, message, image_name = self.build_image(project_name, user_id, temp_dir)
            if not success:
                result['message'] = message
                return result
            
            result['image_name'] = image_name
            
            if callback:
                callback(project_id, 'building', 'Desplegando contenedor...')
            
            # 4. Deploy contenedor
            success, message, port, container_id = self.deploy_container(
                project_id, project_name, user_id, image_name
            )
            
            if not success:
                result['message'] = message
                return result
            
            # Éxito
            result['success'] = True
            result['message'] = 'Proyecto desplegado exitosamente'
            result['port'] = port
            result['container_id'] = container_id
            
            if callback:
                callback(project_id, 'running', f'Desplegado en puerto {port}')
            
            return result
            
        except Exception as e:
            logger.error(f"Error en deploy_project: {e}")
            result['message'] = str(e)
            if callback:
                callback(project_id, 'error', str(e))
            return result
            
        finally:
            # Limpiar directorio temporal
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Error limpiando temp dir: {e}")
    
    def stop_container(self, container_id: str) -> Tuple[bool, str]:
        """Detiene un contenedor"""
        try:
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=10)
            logger.info(f"Contenedor detenido: {container_id[:12]}")
            return True, "Contenedor detenido"
        except Exception as e:
            logger.error(f"Error deteniendo contenedor: {e}")
            return False, str(e)
    
    def remove_container(self, container_id: str) -> Tuple[bool, str]:
        """Elimina un contenedor"""
        try:
            container = self.docker_client.containers.get(container_id)
            container.stop(timeout=5)
            container.remove(force=True)
            logger.info(f"Contenedor eliminado: {container_id[:12]}")
            return True, "Contenedor eliminado"
        except Exception as e:
            logger.error(f"Error eliminando contenedor: {e}")
            return False, str(e)
    
    def get_container_status(self, container_id: str) -> Optional[str]:
        """Obtiene el estado de un contenedor"""
        try:
            container = self.docker_client.containers.get(container_id)
            return container.status
        except:
            return None
