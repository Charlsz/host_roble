"""
Servicio de monitoreo de actividad de contenedores
Apaga contenedores después de 30 minutos de inactividad
"""
import docker
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict

logger = logging.getLogger(__name__)

class ActivityMonitor:
    """Monitor de actividad para auto-shutdown de contenedores"""
    
    def __init__(self, docker_client, inactivity_timeout=1800):  # 30 minutos por defecto
        self.docker_client = docker_client
        self.inactivity_timeout = inactivity_timeout  # segundos
        self.last_activity = {}  # {container_name: timestamp}
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Inicia el monitoreo en un thread separado"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("🔍 Servicio de monitoreo de actividad iniciado")
    
    def stop_monitoring(self):
        """Detiene el monitoreo"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("🛑 Servicio de monitoreo de actividad detenido")
    
    def update_activity(self, container_name: str):
        """Actualiza el timestamp de última actividad de un contenedor"""
        self.last_activity[container_name] = time.time()
        logger.debug(f"📊 Actividad actualizada para {container_name}")
    
    def _monitor_loop(self):
        """Loop principal de monitoreo"""
        logger.info("🔄 Loop de monitoreo iniciado")
        
        while self.monitoring:
            try:
                self._check_inactive_containers()
                time.sleep(60)  # Verificar cada 60 segundos
            except Exception as e:
                logger.error(f"❌ Error en loop de monitoreo: {e}")
                time.sleep(60)
    
    def _check_inactive_containers(self):
        """Verifica y detiene contenedores inactivos"""
        try:
            current_time = time.time()
            containers = self.docker_client.containers.list(
                filters={'name': 'project_'}
            )
            
            for container in containers:
                container_name = container.name
                
                # Si no hay registro de actividad, crearlo con tiempo actual
                if container_name not in self.last_activity:
                    self.last_activity[container_name] = current_time
                    continue
                
                # Calcular tiempo de inactividad
                last_active = self.last_activity[container_name]
                inactive_time = current_time - last_active
                
                # Si supera el timeout, detener contenedor
                if inactive_time > self.inactivity_timeout:
                    logger.info(f"⏱️ Contenedor {container_name} inactivo por {int(inactive_time/60)} minutos")
                    self._stop_container(container)
                    
        except Exception as e:
            logger.error(f"❌ Error verificando contenedores inactivos: {e}")
    
    def _stop_container(self, container):
        """Detiene un contenedor por inactividad"""
        try:
            container_name = container.name
            logger.info(f"🛑 Deteniendo contenedor inactivo: {container_name}")
            container.stop(timeout=10)
            logger.info(f"✅ Contenedor {container_name} detenido exitosamente")
            
            # Eliminar de registro de actividad
            if container_name in self.last_activity:
                del self.last_activity[container_name]
                
        except Exception as e:
            logger.error(f"❌ Error deteniendo contenedor {container.name}: {e}")
    
    def restart_container_if_stopped(self, container_name: str) -> bool:
        """
        Reinicia un contenedor si está detenido
        Usado cuando se recibe una nueva solicitud
        
        Returns:
            True si se reinició, False si ya estaba corriendo o hubo error
        """
        try:
            container = self.docker_client.containers.get(container_name)
            
            if container.status == 'exited':
                logger.info(f"🔄 Reiniciando contenedor: {container_name}")
                container.start()
                self.update_activity(container_name)
                logger.info(f"✅ Contenedor {container_name} reiniciado")
                return True
            else:
                # Ya está corriendo, solo actualizar actividad
                self.update_activity(container_name)
                return False
                
        except docker.errors.NotFound:
            logger.warning(f"⚠️ Contenedor {container_name} no encontrado")
            return False
        except Exception as e:
            logger.error(f"❌ Error reiniciando contenedor {container_name}: {e}")
            return False
    
    def get_inactive_time(self, container_name: str) -> int:
        """
        Obtiene el tiempo de inactividad de un contenedor en segundos
        
        Returns:
            Segundos de inactividad, o 0 si no hay registro
        """
        if container_name not in self.last_activity:
            return 0
        
        current_time = time.time()
        last_active = self.last_activity[container_name]
        return int(current_time - last_active)
