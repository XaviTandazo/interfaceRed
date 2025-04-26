from flask import Flask, render_template, request, redirect, url_for
import paramiko
import time

app = Flask(__name__)

# Función para conectarse al router y retornar el canal interactivo
def connect_router():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.1.1', username='admin', password='cisco')
    return ssh

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
        mac = mac.replace(":", "")
        mac = '.'.join([mac[i:i+4] for i in range(0, len(mac), 4)])

        # Crear un shell interactivo
        shell = ssh.invoke_shell()

        # Enviar comandos al router
        shell.send("config t\n")
        shell.send(f"class-map match-any unwanted-pc\n")
        shell.send(f"match source-address mac {mac}\n")
        shell.send("exit\n")
        shell.send("policy-map block\n")
        shell.send("class unwanted-pc\n")
        shell.send("drop\n")
        shell.send("exit\n")
        shell.send("interface FastEthernet1/0\n")
        shell.send("service-policy input block\n")
        shell.send("exit\n")
        shell.send("end\n")
        shell.send("write memory\n")

        # Esperar un momento para que todos los comandos se ejecuten
        import time
        time.sleep(2)

        # Leer la salida para depuración (opcional)
        output = shell.recv(10000).decode()
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
    ssh.close()
    return redirect(url_for('index'))

@app.route('/block_device', methods=['POST'])
def block_device():
    mac = request.form['mac_address']
    try:
        ssh = connect_router()
        success = block_mac(ssh, mac)
        ssh.close()
        msg = "Dispositivo bloqueado exitosamente" if success else "Error al bloquear la MAC"
        return render_template('index.html', message=msg)
    except Exception as e:
        return render_template('index.html', message=f"Error: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
