#!/usr/bin/env python3
"""
Script de limpieza de contenedores dinámicos para ROBLE Microservices
Ejecutar antes de docker-compose up para limpiar contenedores anteriores
"""

import docker
import sys
import os

def cleanup_dynamic_containers():
    """Limpia contenedores dinámicos para evitar conflictos de puertos"""
    print("🧹 LIMPIEZA DE CONTENEDORES DINÁMICOS")
    print("=" * 50)
    
    try:
        # Conectar a Docker
        docker_client = docker.from_env()
        print("✅ Conectado a Docker")
    except Exception as e:
        print(f"❌ Error conectando con Docker: {e}")
        return False
    
    try:
        # Buscar todos los contenedores y filtrar por nombre que contenga 'dynamic_'
        print("🔍 Buscando contenedores dinámicos...")
        all_containers = docker_client.containers.list(all=True)
        containers = [c for c in all_containers if 'dynamic_' in c.name]
        
        print(f"📊 Encontrados {len(containers)} contenedores dinámicos")
        
        if containers:
            print("🧹 Limpiando contenedores...")
            
            for container in containers:
                try:
                    container_name = container.name
                    print(f"  🔄 Procesando: {container_name}")
                    
                    # Detener si está corriendo
                    if container.status == 'running':
                        container.stop()
                        print(f"    ⏹️ Detenido")
                    
                    # Eliminar el contenedor
                    container.remove()
                    print(f"    🗑️ Eliminado")
                    
                except Exception as e:
                    print(f"    ❌ Error: {e}")
            
            # Limpiar imágenes de microservicios también
            print("🖼️ Limpiando imágenes de microservicios...")
            try:
                images = docker_client.images.list(filters={"reference": "microservice_*"})
                print(f"📊 Encontradas {len(images)} imágenes de microservicios")
                
                for image in images:
                    try:
                        image_tags = image.tags if image.tags else ["<none>"]
                        docker_client.images.remove(image.id, force=True)
                        print(f"  🗑️ Imagen eliminada: {image_tags[0]}")
                    except Exception as e:
                        print(f"  ❌ Error eliminando imagen: {e}")
                        
            except Exception as e:
                print(f"❌ Error limpiando imágenes: {e}")
                
            print("✅ Limpieza de contenedores dinámicos completada")
        else:
            print("✨ No hay contenedores dinámicos para limpiar")
            
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
        print("=" * 50)
        return False

def main():
    """Función principal"""
    print()
    print("🚀 ROBLE MICROSERVICES - LIMPIEZA AUTOMÁTICA")
    print("🔧 Limpiando contenedores dinámicos antes del inicio...")
    print()
    
    success = cleanup_dynamic_containers()
    
    if success:
        print("✅ Limpieza completada exitosamente")
        print("💡 Ahora puedes ejecutar: docker-compose up")
        sys.exit(0)
    else:
        print("❌ Error durante la limpieza")
        print("⚠️ Revisa los errores antes de continuar")
        sys.exit(1)

if __name__ == '__main__':
    main()