from flask import Flask, render_template, request, redirect, url_for
import paramiko

app = Flask(__name__)

# Función para conectarse al router con configuraciones compatibles
def connect_router():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    transport = paramiko.Transport(('192.168.1.1', 22))
    transport.get_security_options().ciphers = ['aes128-cbc']
    transport.get_security_options().kex = ['diffie-hellman-group14-sha1']
    transport.get_security_options().host_key_algorithms = ['ssh-rsa']

    transport.connect(username='admin', password='cisco')
    ssh._transport = transport
    return ssh

# Página principal
@app.route('/')
def index():
    return render_template('index.html')

# Agregar dispositivo autorizado (permitir MAC)
@app.route('/add_device', methods=['POST'])
def add_device():
    mac_address = request.form['mac_address']
    interface = "FastEthernet1/1"  # Puedes hacerlo dinámico si quieres

    ssh = connect_router()
    commands = f'''
    conf t
    interface {interface}
    switchport port-security
    switchport port-security mac-address {mac_address}
    end
    write memory
    '''
    ssh.exec_command(commands)
    ssh.close()
    return redirect(url_for('index'))

# Bloquear dispositivo (ponerlo como no permitido)
@app.route('/block_device', methods=['POST'])
def block_device():
    mac_address = request.form['mac_address']
    interface = "FastEthernet1/1"

    ssh = connect_router()
    commands = f'''
    conf t
    interface {interface}
    switchport port-security mac-address {mac_address}
    switchport port-security violation shutdown
    end
    write memory
    '''
    ssh.exec_command(commands)
    ssh.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
