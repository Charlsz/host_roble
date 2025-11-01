"""
Endpoints de Autenticación para la plataforma de Hosting
Integración con ROBLE para login, signup y gestión de sesiones
"""
from flask import Blueprint, request, jsonify
import logging
import sys
import os

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

from roble_client import RobleClient

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
logger = logging.getLogger(__name__)

# Instancia del cliente ROBLE
roble = RobleClient()

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login de usuario con ROBLE
    
    Body:
        email: Correo electrónico
        password: Contraseña
        
    Returns:
        accessToken, refreshToken y datos del usuario
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email y password son requeridos'}), 400
        
        # Autenticar con ROBLE
        auth_response = roble.login(email, password)
        
        # Verificar token y obtener datos del usuario
        user_info = roble.verify_token(auth_response['accessToken'])
        
        return jsonify({
            'success': True,
            'accessToken': auth_response['accessToken'],
            'refreshToken': auth_response['refreshToken'],
            'user': user_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error en login: {e}")
        return jsonify({'error': str(e)}), 401

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """
    Registro de nuevo usuario (sin verificación de email)
    
    Body:
        email: Correo electrónico
        password: Contraseña (mínimo 6 caracteres)
        name: Nombre completo
        
    Returns:
        Confirmación de registro
    """
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        
        if not email or not password or not name:
            return jsonify({'error': 'Email, password y nombre son requeridos'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'La contraseña debe tener al menos 6 caracteres'}), 400
        
        # Registrar en ROBLE (signup-direct para pruebas sin verificación)
        roble.signup_direct(email, password, name)
        
        return jsonify({
            'success': True,
            'message': 'Usuario registrado exitosamente. Ya puedes iniciar sesión.'
        }), 201
        
    except Exception as e:
        logger.error(f"Error en signup: {e}")
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Cierra la sesión del usuario
    
    Headers:
        Authorization: Bearer {accessToken}
        
    Returns:
        Confirmación de logout
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token no proporcionado'}), 401
        
        access_token = auth_header.split(' ')[1]
        
        # Logout en ROBLE
        roble.logout(access_token)
        
        return jsonify({
            'success': True,
            'message': 'Sesión cerrada exitosamente'
        }), 200
        
    except Exception as e:
        logger.error(f"Error en logout: {e}")
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """
    Obtiene información del usuario actual
    
    Headers:
        Authorization: Bearer {accessToken}
        
    Returns:
        Información del usuario autenticado
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token no proporcionado'}), 401
        
        access_token = auth_header.split(' ')[1]
        
        # Verificar token y obtener datos
        user_info = roble.verify_token(access_token)
        
        return jsonify({
            'success': True,
            'user': user_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error al obtener usuario: {e}")
        return jsonify({'error': 'Token inválido o expirado'}), 401

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """
    Refresca el accessToken usando el refreshToken
    
    Body:
        refreshToken: Token de refresh
        
    Returns:
        Nuevo accessToken
    """
    try:
        data = request.get_json()
        refresh_token = data.get('refreshToken')
        
        if not refresh_token:
            return jsonify({'error': 'refreshToken es requerido'}), 400
        
        # Obtener nuevo token
        new_tokens = roble.refresh_token(refresh_token)
        
        return jsonify({
            'success': True,
            'accessToken': new_tokens.get('accessToken')
        }), 200
        
    except Exception as e:
        logger.error(f"Error al refrescar token: {e}")
        return jsonify({'error': str(e)}), 401

@auth_bp.route('/verify', methods=['GET'])
def verify_token():
    """
    Verifica si un token es válido (útil para middleware)
    
    Headers:
        Authorization: Bearer {accessToken}
        
    Returns:
        Estado de validez del token
    """
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'valid': False}), 401
        
        access_token = auth_header.split(' ')[1]
        
        # Verificar token
        user_info = roble.verify_token(access_token)
        
        return jsonify({
            'valid': True,
            'user': user_info
        }), 200
        
    except Exception as e:
        return jsonify({'valid': False}), 401
