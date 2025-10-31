#!/usr/bin/env python3
"""
Script de prueba para verificar conexión con ROBLE
"""
import requests
import json

ROBLE_BASE_HOST = "https://roble-api.openlab.uninorte.edu.co"
ROBLE_CONTRACT = "microservices_roble_e65ac352d7"

def test_roble_connection():
    """Prueba la conexión básica con ROBLE"""
    print("🔍 Probando conexión con ROBLE...")
    
    # Probar endpoint básico
    try:
        url = f"{ROBLE_BASE_HOST}/health"
        print(f"Probando: {url}")
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Conexión básica exitosa")
        else:
            print(f"❌ Error en conexión básica: {response.status_code}")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

def test_roble_login_endpoint():
    """Prueba el endpoint de login específico"""
    print(f"\n🔍 Probando endpoint de login...")
    
    url = f"{ROBLE_BASE_HOST}/auth/{ROBLE_CONTRACT}/login"
    print(f"URL de login: {url}")
    
    # Intentar con credenciales de prueba
    test_data = {
        "email": "test@test.com",
        "password": "test123"
    }
    
    try:
        response = requests.post(url, json=test_data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("✅ Endpoint funciona (401 es esperado con credenciales falsas)")
        elif response.status_code == 200:
            print("✅ Login exitoso (inesperado con credenciales de prueba)")
        else:
            print(f"❌ Error inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error al probar login: {e}")

def test_contract_validity():
    """Prueba si el contrato existe"""
    print(f"\n🔍 Verificando contrato: {ROBLE_CONTRACT}")
    
    # Probar endpoint de información del contrato
    try:
        url = f"{ROBLE_BASE_HOST}/contracts/{ROBLE_CONTRACT}"
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Contrato válido")
            print(f"Info: {response.text[:200]}...")
        elif response.status_code == 404:
            print("❌ Contrato no encontrado")
        else:
            print(f"❌ Error al verificar contrato: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error al verificar contrato: {e}")

if __name__ == "__main__":
    print("=== PRUEBA DE CONEXIÓN ROBLE ===")
    print(f"Host: {ROBLE_BASE_HOST}")
    print(f"Contract: {ROBLE_CONTRACT}")
    print("=" * 40)
    
    test_roble_connection()
    test_contract_validity()
    test_roble_login_endpoint()
    
    print("\n=== FIN DE PRUEBAS ===")