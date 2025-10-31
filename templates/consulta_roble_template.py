"""
Microservicio Consulta Roble - Template
Función que consulta datos específicos de ROBLE
"""
import os
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Variables de entorno ROBLE
ROBLE_BASE_HOST = os.getenv('ROBLE_BASE_HOST', 'https://roble-api.openlab.uninorte.edu.co')
ROBLE_CONTRACT = os.getenv('ROBLE_CONTRACT', 'microservices_roble_e65ac352d7')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'consulta-roble'})

def consulta_roble():
    """
    Función que recibe:
    - Nombre del proyecto en Roble
    - Token 
    - Nombre de la tabla
    
    Y retorna el contenido de dicha tabla
    """
    # Obtener datos de la petición
    json_data = request.get_json() or {}
    
    # Parámetros requeridos
    proyecto_nombre = json_data.get('proyecto_nombre', ROBLE_CONTRACT)
    token = json_data.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
    tabla_nombre = json_data.get('tabla_nombre', 'usuarios')
    
    if not token:
        return {'error': 'Token requerido', 'parametros_requeridos': ['token', 'tabla_nombre']}
    
    try:
        # Hacer consulta a ROBLE
        url = f"{ROBLE_BASE_HOST}/database/{proyecto_nombre}/read"
        params = {"tableName": tabla_nombre}
        
        response = requests.get(
            url, 
            headers={"Authorization": f"Bearer {token}"}, 
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'exito': True,
                'proyecto': proyecto_nombre,
                'tabla': tabla_nombre,
                'total_registros': len(data) if isinstance(data, list) else 1,
                'datos': data
            }
        else:
            return {
                'error': f'Error consultando ROBLE: {response.status_code}',
                'mensaje': response.text
            }
            
    except Exception as e:
        return {'error': f'Error de conexión: {str(e)}'}

@app.route('/consulta', methods=['POST'])
def consulta_endpoint():
    """Endpoint para la función consulta_roble()"""
    try:
        resultado = consulta_roble()
        return jsonify({
            'resultado': resultado,
            'funcion': 'consulta_roble',
            'servicio': 'consulta-roble'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_data():
    """Endpoint genérico de procesamiento"""
    try:
        resultado = consulta_roble()
        return jsonify({
            'resultado': resultado,
            'funcion': 'consulta_roble',
            'servicio': 'consulta-roble'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)