from flask import Flask, render_template, request, redirect, url_for
import paramiko
import time
import re

app = Flask(__name__)

# Función para conectarse al router y retornar el canal interactivo
def connect_router():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect('192.168.1.1', username='admin', password='cisco')
        return ssh
    except Exception as e:
        print(f"Error al conectar al router: {e}")
        return None

# Ejecutar comandos en un canal interactivo y retornar salida
def send_commands(channel, commands):
    output = ""
    for cmd in commands:
        channel.send(cmd + "\n")
        time.sleep(1)  # Espera para que el router procese el comando
        while channel.recv_ready():
            output += channel.recv(1024).decode()
    return output

# Comando para bloquear una MAC usando class-map y policy-map
def block_mac(ssh, mac):
    try:
        # Validar y formatear la MAC
        mac = mac.replace(":", "")
        if not re.match(r'^[0-9a-fA-F]{12}$', mac):  # Asegura que sea una MAC válida
            return False

        mac = '.'.join([mac[i:i+4] for i in range(0, len(mac), 4)])

        # Crear un shell interactivo
        shell = ssh.invoke_shell()

        # Enviar comandos al router
        commands = [
            "config t",
            f"class-map match-any unwanted-pc",
            f"match source-address mac {mac}",
            "exit",
            "policy-map block",
            "class unwanted-pc",
            "drop",
            "exit",
            "interface FastEthernet1/0",
            "service-policy input block",
            "exit",
            "end",
            "write memory"
        ]
        
        # Enviar los comandos y obtener la salida
        output = send_commands(shell, commands)

        # Esperar un momento para que todos los comandos se ejecuten
        time.sleep(2)

        # Leer la salida para depuración (opcional)
        print(output)

        return True
    except Exception as e:
        print(f"Error al bloquear la MAC: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_device', methods=['POST'])
def add_device():
    mac = request.form['mac_address']
    ssh = connect_router()
    if ssh:
        success = block_mac(ssh, mac)
        ssh.close()
        msg = "Dispositivo agregado exitosamente" if success else "Error al agregar la MAC"
        return render_template('index.html', message=msg)
    else:
        return render_template('index.html', message="No se pudo conectar al router.")

@app.route('/block_device', methods=['POST'])
def block_device():
    mac = request.form['mac_address']
    try:
        ssh = connect_router()
        if not ssh:
            return render_template('index.html', message="No se pudo conectar al router.")

        success = block_mac(ssh, mac)
        ssh.close()
        msg = "Dispositivo bloqueado exitosamente" if success else "Error al bloquear la MAC"
        return render_template('index.html', message=msg)
    except Exception as e:
        return render_template('index.html', message=f"Error: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
