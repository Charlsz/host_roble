"""
Microservicio Suma - Template
Función que suma dos valores recibidos como parámetros
"""
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'suma'})

def sumar():
    """Función suma de dos valores requerida"""
    # Obtener parámetros desde la URL o desde el cuerpo de la petición
    args = request.args
    json_data = request.get_json() or {}
    
    # Obtener 'a' y 'b' desde la URL: /sumar?a=10&b=20
    a = args.get('a', default=0, type=int)
    b = args.get('b', default=0, type=int)
    
    # Si no están en la URL, intentar desde JSON: {"a": 10, "b": 20}
    if a == 0 and b == 0:
        a = json_data.get('a', 0)
        b = json_data.get('b', 0)
    
    resultado = a + b
    return f"La suma de {a} y {b} es: {resultado}"

@app.route('/sumar', methods=['GET', 'POST'])
def sumar_endpoint():
    """Endpoint para la función sumar()"""
    try:
        resultado = sumar()
        return jsonify({
            'resultado': resultado,
            'funcion': 'sumar',
            'servicio': 'suma'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_data():
    """Endpoint genérico de procesamiento"""
    try:
        resultado = sumar()
        return jsonify({
            'resultado': resultado,
            'funcion': 'sumar',
            'servicio': 'suma'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)