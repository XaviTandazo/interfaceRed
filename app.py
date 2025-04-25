from flask import Flask, render_template, request, redirect, url_for
import paramiko

app = Flask(__name__)

# Función para conectarse al router con parámetros de compatibilidad
def connect_router():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Acepta automáticamente la clave del host

    # Establece una conexión SSH con el router
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
    command = f"mac access-list extended ARP_Packet permit host {mac_address}"
    ssh.exec_command(command)  # Ejecutar comando para permitir MAC
    ssh.close()
    return redirect(url_for('index'))

# Bloquear un dispositivo
@app.route('/block_device', methods=['POST'])
def block_device():
    mac_address = request.form['mac_address']
    # Conexión SSH al router y actualización de las reglas de filtrado
    ssh = connect_router()
    
    # Comando para bloquear la MAC
    command = f"mac access-list extended ARP_Packet deny host {mac_address}"
    ssh.exec_command(command)  # Ejecutar comando para bloquear MAC

    # Aplicar la lista de acceso a la interfaz (ajusta 'gi 0/1' con la interfaz adecuada)
    apply_acl_command = "interface gi 0/1"
    ssh.exec_command(apply_acl_command)
    ssh.exec_command(f"bridge-group input-address-list ARP_Packet")

    # Salir de la configuración
    ssh.exec_command("end")
    ssh.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
