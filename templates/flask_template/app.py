from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    return '<h1>Plantilla Flask</h1><p>Hola desde Flask! Esta es una plantilla mínima.</p>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
