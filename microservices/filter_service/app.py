"""
Filter Service - Microservicio de Filtrado de Usuarios ROBLE
Filtra usuarios según criterios específicos
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
SERVICE_NAME = os.getenv('SERVICE_NAME', 'filter-service')

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

def roble_get_users(token, filters=None):
    """Obtener usuarios de ROBLE"""
    try:
        url = f"{ROBLE_BASE_HOST}/database/{ROBLE_CONTRACT}/read"
        params = {"tableName": "usuarios"}
        if filters:
            params.update(filters)
        
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
def process_filter_users(token, filter_data):
    """Procesa filtrado de usuarios"""
    filter_field = filter_data.get('filter_field', 'active')
    filter_value = filter_data.get('filter_value', True)
    limit = filter_data.get('limit', 100)
    
    # Obtener usuarios de ROBLE
    filters = {filter_field: filter_value} if filter_field and filter_value is not None else {}
    users = roble_get_users(token, filters)
    
    # Aplicar límite
    users = users[:limit]
    
    # Procesar datos
    result = []
    for user in users:
        result.append({
            'id': user.get('_id'),
            'name': user.get('name'),
            'email': user.get('email'),
            'age': user.get('age'),
            'city': user.get('city'),
            'active': user.get('active')
        })
    
    return {
        "success": True,
        "service": SERVICE_NAME,
        "filter_criteria": {"field": filter_field, "value": filter_value},
        "total_results": len(result),
        "users": result,
        "processed_at": datetime.now().isoformat()
    }

# --- API ENDPOINTS ---
@app.route('/')
def home():
    """Información del servicio"""
    return jsonify({
        "service": SERVICE_NAME,
        "type": "filter",
        "description": "Microservicio de filtrado de usuarios ROBLE",
        "version": "1.0",
        "endpoints": {
            "filter": "/filter",
            "health": "/health"
        }
    })

@app.route('/filter', methods=['POST'])
def filter_users():
    """Endpoint principal de filtrado"""
    # Verificar token
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "Token de autorización requerido"}), 401
    
    token = auth_header.split(' ')[1]
    if not roble_verify_token(token):
        return jsonify({"error": "Token inválido o expirado"}), 401
    
    if not roble_check_permissions(token):
        return jsonify({"error": "Permisos insuficientes"}), 403
    
    # Obtener datos de filtrado
    data = request.get_json() or {}
    
    try:
        result = process_filter_users(token, data)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error procesando filtrado: {e}")
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
    print(f"🔍 {SERVICE_NAME} ready")
    app.run(host='0.0.0.0', port=5000, debug=False)