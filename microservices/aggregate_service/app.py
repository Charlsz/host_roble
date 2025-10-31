"""
Aggregate Service - Microservicio de Agregación de Datos ROBLE
Agrega y procesa estadísticas de usuarios
"""
import os
import logging
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json

# Configuración
app = Flask(__name__)
CORS(app, origins=['http://localhost:8080', 'http://127.0.0.1:8080'])
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variables de entorno
ROBLE_BASE_HOST = os.getenv('ROBLE_BASE_HOST', 'https://roble-api.openlab.uninorte.edu.co')
ROBLE_CONTRACT = os.getenv('ROBLE_CONTRACT', 'microservices_roble_e65ac352d7')
SERVICE_NAME = os.getenv('SERVICE_NAME', 'aggregate-service')

# --- FUNCIONES ROBLE ---
def roble_verify_token(token):
    """Verificar token en ROBLE"""
    try:
        url = f"{ROBLE_BASE_HOST}/auth/{ROBLE_CONTRACT}/verify-token"
        response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        return response.status_code == 200
    except:
        return False

def roble_check_permissions(token):
    """Verificar permisos específicos del usuario"""
    try:
        url = f"{ROBLE_BASE_HOST}/auth/{ROBLE_CONTRACT}/verify-token"
        response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        
        if response.status_code == 200:
            user_data = response.json()
            user_role = user_data.get('role', 'user')
            # Permitir acceso básico a todos los roles autenticados
            return True
        return False
    except:
        return False

def roble_get_users(token):
    """Obtener usuarios de ROBLE"""
    try:
        url = f"{ROBLE_BASE_HOST}/database/{ROBLE_CONTRACT}/read"
        params = {"tableName": "usuarios"}
        
        response = requests.get(url, 
            headers={"Authorization": f"Bearer {token}"}, 
            params=params
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error obteniendo usuarios: {e}")
        return []

# --- PROCESAMIENTO ---
def process_aggregate_data(token, aggregate_data):
    """Procesa agregación de datos"""
    users = roble_get_users(token)
    
    group_by = aggregate_data.get('group_by', 'city')
    
    # Agrupar por campo
    groups = {}
    for user in users:
        key = user.get(group_by, 'unknown')
        if key not in groups:
            groups[key] = 0
        groups[key] += 1
    
    # Calcular estadísticas adicionales
    stats = {
        "total_users": len(users),
        "groups_count": len(groups),
        "average_per_group": len(users) / len(groups) if groups else 0,
        "largest_group": max(groups.values()) if groups else 0,
        "smallest_group": min(groups.values()) if groups else 0
    }
    
    return {
        "success": True,
        "service": SERVICE_NAME,
        "group_by": group_by,
        "statistics": stats,
        "groups": groups,
        "processed_at": datetime.now().isoformat()
    }

# --- API ENDPOINTS ---
@app.route('/')
def home():
    """Información del servicio"""
    return jsonify({
        "service": SERVICE_NAME,
        "type": "aggregate",
        "description": "Microservicio de agregación de datos ROBLE",
        "version": "1.0",
        "endpoints": {
            "aggregate": "/aggregate",
            "health": "/health"
        }
    })

@app.route('/aggregate', methods=['POST'])
def aggregate_data():
    """Endpoint principal de agregación"""
    # Verificar token
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Token de autorización requerido"}), 401
    
    token = auth_header.split(' ')[1]
    if not roble_verify_token(token):
        return jsonify({"error": "Token inválido o expirado"}), 401
    
    if not roble_check_permissions(token):
        return jsonify({"error": "Permisos insuficientes"}), 403
    
    # Obtener datos de agregación
    data = request.get_json() or {}
    
    try:
        result = process_aggregate_data(token, data)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error procesando agregación: {e}")
        return jsonify({
            "error": "Error interno del servidor",
            "service": SERVICE_NAME
        }), 500

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "service": SERVICE_NAME,
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print(f"📊 {SERVICE_NAME} ready")
    app.run(host='0.0.0.0', port=5000, debug=False)