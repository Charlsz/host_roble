"""
Microservicio Hola Mundo - Template
Función simple que retorna "Hola Mundo"
"""
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'hola-mundo'})

def hola():
    """Función Hola Mundo requerida"""
    return "Hola Mundo"

@app.route('/hola', methods=['GET', 'POST'])
def hola_endpoint():
    """Endpoint para la función hola()"""
    try:
        resultado = hola()
        return jsonify({
            'resultado': resultado,
            'funcion': 'hola',
            'servicio': 'hola-mundo'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_data():
    """Endpoint genérico de procesamiento"""
    try:
        resultado = hola()
        return jsonify({
            'resultado': resultado,
            'funcion': 'hola',
            'servicio': 'hola-mundo'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)