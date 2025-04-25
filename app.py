from flask import Flask, render_template, request, redirect, url_for
import paramiko

app = Flask(__name__)

# Función para conectarse al router con parámetros de compatibilidad
def connect_router():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Realizamos la conexión SSH utilizando las configuraciones predeterminadas
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
    mac_address = mac_address.lower()  # Convertimos la MAC a minúsculas para evitar errores de mayúsculas/minúsculas
    
    # Conexión SSH al router y actualización de la lista MAC
    ssh = connect_router()
    # Aquí el comando real para agregar la MAC a la lista de dispositivos permitidos
    ssh.exec_command(f'arp access-list {mac_address} permit')
    ssh.close()
    return redirect(url_for('index'))

# Bloquear un dispositivo
@app.route('/block_device', methods=['POST'])
def block_device():
    mac_address = request.form['mac_address']
    mac_address = mac_address.lower()  # Convertimos la MAC a minúsculas para evitar errores de mayúsculas/minúsculas
    
    # Conexión SSH al router y actualización de las reglas de filtrado
    ssh = connect_router()
    # Aquí el comando real para bloquear la MAC en el router
    ssh.exec_command(f'arp access-list {mac_address} deny')
    ssh.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
