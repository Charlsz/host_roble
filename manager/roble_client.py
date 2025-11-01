"""
Cliente para interactuar con la API de ROBLE
Maneja autenticación y operaciones de base de datos
"""
import os
import requests
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class RobleClient:
    """Cliente para consumir la API de ROBLE"""
    
    def __init__(self):
        self.base_host = os.getenv('ROBLE_BASE_HOST', 'https://roble-api.openlab.uninorte.edu.co')
        self.contract = os.getenv('ROBLE_CONTRACT', 'microservices_roble_e65ac352d7')
        self.auth_url = f"{self.base_host}/auth/{self.contract}"
        self.db_url = f"{self.base_host}/database/{self.contract}"
        
    # ==================== AUTENTICACIÓN ====================
    
    def login(self, email: str, password: str) -> Dict:
        """
        Autentica un usuario con ROBLE
        
        Args:
            email: Correo electrónico del usuario
            password: Contraseña del usuario
            
        Returns:
            Dict con accessToken y refreshToken
        """
        try:
            response = requests.post(
                f"{self.auth_url}/login",
                json={"email": email, "password": password}
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"✅ Login exitoso para: {email}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error en login: {e}")
            raise
    
    def signup_direct(self, email: str, password: str, name: str) -> bool:
        """
        Registra un nuevo usuario sin verificación de email
        
        Args:
            email: Correo electrónico
            password: Contraseña (mínimo 6 caracteres)
            name: Nombre completo
            
        Returns:
            True si el registro fue exitoso
        """
        try:
            response = requests.post(
                f"{self.auth_url}/signup-direct",
                json={
                    "email": email,
                    "password": password,
                    "name": name
                }
            )
            response.raise_for_status()
            logger.info(f"✅ Usuario registrado: {email}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error en registro: {e}")
            raise
    
    def get_user_info(self, access_token: str) -> Dict:
        """
        Obtiene la información del usuario autenticado
        
        Args:
            access_token: Token de acceso
            
        Returns:
            Dict con información del usuario
        """
        try:
            response = requests.get(
                f"{self.auth_url}/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error obteniendo info de usuario: {e}")
            raise
    
    def refresh_token(self, refresh_token: str) -> Dict:
        """
        Obtiene un nuevo accessToken usando el refreshToken
        
        Args:
            refresh_token: Token de refresh
            
        Returns:
            Dict con nuevo accessToken
        """
        try:
            response = requests.post(
                f"{self.auth_url}/refresh-token",
                json={"refreshToken": refresh_token}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error al refrescar token: {e}")
            raise
    
    def verify_token(self, access_token: str) -> Dict:
        """
        Verifica si un token es válido
        
        Args:
            access_token: Token a verificar
            
        Returns:
            Dict con información del usuario si es válido
        """
        try:
            response = requests.get(
                f"{self.auth_url}/verify-token",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Token inválido: {e}")
            raise
    
    def logout(self, access_token: str) -> bool:
        """
        Cierra la sesión del usuario
        
        Args:
            access_token: Token de acceso del usuario
            
        Returns:
            True si el logout fue exitoso
        """
        try:
            response = requests.post(
                f"{self.auth_url}/logout",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            logger.info("✅ Logout exitoso")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error en logout: {e}")
            raise
    
    # ==================== BASE DE DATOS ====================
    
    def insert_records(self, table_name: str, records: List[Dict], access_token: str) -> Dict:
        """
        Inserta múltiples registros en una tabla
        
        Args:
            table_name: Nombre de la tabla
            records: Lista de diccionarios con los datos
            access_token: Token de autenticación
            
        Returns:
            Dict con registros insertados y omitidos
        """
        try:
            response = requests.post(
                f"{self.db_url}/insert",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "tableName": table_name,
                    "records": records
                }
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"✅ Insertados {len(data.get('inserted', []))} registros en {table_name}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error al insertar en {table_name}: {e}")
            raise
    
    def read_records(self, table_name: str, filters: Optional[Dict] = None, access_token: str = None) -> List[Dict]:
        """
        Lee registros de una tabla con filtros opcionales
        
        Args:
            table_name: Nombre de la tabla
            filters: Diccionario con filtros (campo=valor) - Se aplican localmente
            access_token: Token de autenticación
            
        Returns:
            Lista de registros filtrados
        """
        try:
            params = {"tableName": table_name}
            
            headers = {}
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
            
            response = requests.get(
                f"{self.db_url}/read",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            
            # Aplicar filtros localmente si existen
            if filters:
                filtered_data = []
                for record in data:
                    match = True
                    for key, value in filters.items():
                        if record.get(key) != value:
                            match = False
                            break
                    if match:
                        filtered_data.append(record)
                data = filtered_data
            
            logger.info(f"✅ Leídos {len(data)} registros de {table_name}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error al leer {table_name}: {e}")
            raise
    
    def update_record(self, table_name: str, id_column: str, id_value: str, 
                     updates: Dict, access_token: str) -> Dict:
        """
        Actualiza un registro específico
        
        Args:
            table_name: Nombre de la tabla
            id_column: Nombre de la columna identificadora (ej: _id)
            id_value: Valor del identificador
            updates: Diccionario con campos a actualizar
            access_token: Token de autenticación
            
        Returns:
            Registro actualizado
        """
        try:
            response = requests.put(
                f"{self.db_url}/update",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "tableName": table_name,
                    "idColumn": id_column,
                    "idValue": id_value,
                    "updates": updates
                }
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"✅ Actualizado registro en {table_name}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error al actualizar {table_name}: {e}")
            raise
    
    def delete_record(self, table_name: str, id_column: str, id_value: str, 
                     access_token: str) -> Dict:
        """
        Elimina un registro específico
        
        Args:
            table_name: Nombre de la tabla
            id_column: Nombre de la columna identificadora
            id_value: Valor del identificador
            access_token: Token de autenticación
            
        Returns:
            Registro eliminado
        """
        try:
            response = requests.delete(
                f"{self.db_url}/delete",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "tableName": table_name,
                    "idColumn": id_column,
                    "idValue": id_value
                }
            )
            response.raise_for_status()
            data = response.json()
            logger.info(f"✅ Eliminado registro de {table_name}")
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error al eliminar de {table_name}: {e}")
            raise
    
    # ==================== HELPERS ESPECÍFICOS ====================
    
    def create_project(self, user_id: str, nombre: str, repo_url: str, access_token: str) -> Dict:
        """
        Crea un nuevo proyecto para un usuario
        
        Args:
            user_id: ID del usuario (del token)
            nombre: Nombre del proyecto
            repo_url: URL del repositorio GitHub
            access_token: Token de autenticación
            
        Returns:
            Proyecto creado
        """
        records = [{
            "user_id": user_id,
            "nombre": nombre,
            "repo_url": repo_url,
            "status": "pending"
        }]
        
        result = self.insert_records("proyectos", records, access_token)
        if result.get("inserted"):
            return result["inserted"][0]
        else:
            raise Exception(f"Error al crear proyecto: {result.get('skipped')}")
    
    def get_user_projects(self, user_id: str, access_token: str) -> List[Dict]:
        """
        Obtiene todos los proyectos de un usuario
        
        Args:
            user_id: ID del usuario
            access_token: Token de autenticación
            
        Returns:
            Lista de proyectos del usuario
        """
        return self.read_records("proyectos", {"user_id": user_id}, access_token)
    
    def update_project_status(self, project_id: str, status: str, 
                            container_id: Optional[str] = None, 
                            access_token: str = None) -> Dict:
        """
        Actualiza el estado de un proyecto
        
        Args:
            project_id: ID del proyecto
            status: Nuevo estado
            container_id: ID del contenedor (opcional)
            access_token: Token de autenticación
            
        Returns:
            Proyecto actualizado
        """
        updates = {"status": status}
        if container_id:
            updates["container_id"] = container_id
        
        return self.update_record("proyectos", "_id", project_id, updates, access_token)
    
    def create_container_info(self, project_id: str, port: int, 
                            image_name: str, access_token: str) -> Dict:
        """
        Crea información de contenedor asociado a un proyecto
        
        Args:
            project_id: ID del proyecto
            port: Puerto asignado
            image_name: Nombre de la imagen Docker
            access_token: Token de autenticación
            
        Returns:
            Info del contenedor creada
        """
        records = [{
            "project_id": project_id,
            "port": port,
            "status": "stopped",
            "cpu_limit": "0.5",
            "memory_limit": "256m",
            "image_name": image_name
        }]
        
        result = self.insert_records("containers", records, access_token)
        if result.get("inserted"):
            return result["inserted"][0]
        else:
            raise Exception(f"Error al crear container: {result.get('skipped')}")
