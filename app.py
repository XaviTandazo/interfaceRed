from flask import Flask, render_template, request, redirect, url_for
import paramiko

app = Flask(__name__)

# Función para conectarse al router
def connect_router():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.1.1', username='admin', password='cisco')
    return ssh

# Página principal
@app.route('/')
def index():
    return render_template('index.html')

# Agregar un dispositivo autorizado
@app.route('/add_device', methods=['POST'])
def add_device():
    mac_address = request.form['mac_address']
    # Conexión SSH al router y actualización de la lista MAC
    ssh = connect_router()
    ssh.exec_command(f'command_to_add_mac {mac_address}')
    ssh.close()
    return redirect(url_for('index'))

# Bloquear un dispositivo
@app.route('/block_device', methods=['POST'])
def block_device():
    mac_address = request.form['mac_address']
    # Conexión SSH al router y actualización de las reglas de filtrado
    ssh = connect_router()
    ssh.exec_command(f'command_to_block_mac {mac_address}')
    ssh.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
