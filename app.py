from flask import Flask, render_template, request, redirect, url_for
import paramiko

app = Flask(__name__)

# Función para conectarse al router con parámetros de compatibilidad
def connect_router():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Establece una conexión con configuraciones predeterminadas de seguridad
    ssh.connect('192.168.1.1', username='admin', password='cisco')

    return ssh

# Comando para bloquear una MAC usando class-map y policy-map
def block_mac(ssh, mac):
    try:
        # Eliminar los dos puntos y poner los puntos entre bloques de 4 caracteres
        mac = mac.replace(":", "")
        mac = '.'.join([mac[i:i+4] for i in range(0, len(mac), 4)])

        # Iniciar el modo de configuración
        ssh.exec_command("conf t\n")
        
        # Configurar el class-map
        class_map_command = f"class-map match-any unwanted-pc\nmatch source-address mac {mac}\nexit"
        ssh.exec_command(class_map_command)
        
        # Configurar el policy-map
        policy_map_command = "policy-map block\nclass unwanted-pc\ndrop\nexit"
        ssh.exec_command(policy_map_command)
        
        # Aplicar el policy-map a la interfaz
        interface_command = "interface FastEthernet1/0\nservice-policy input block\nexit"
        ssh.exec_command(interface_command)
        
        # Salir de la configuración
        ssh.exec_command("end\n")
        
        return True
    except Exception as e:
        print(f"Error al bloquear la MAC: {e}")
        return False

# Página principal
@app.route('/')
def index():
    return render_template('index.html')

# Agregar un dispositivo autorizado
@app.route('/add_device', methods=['POST'])
def add_device():
    mac = request.form['mac_address']  # Cambié 'mac_address' aquí
    # Conexión SSH al router y actualización de la lista MAC
    ssh = connect_router()
    # Aquí puedes implementar el código para agregar la MAC a una lista permitida si es necesario
    ssh.close()
    return redirect(url_for('index'))

# Bloquear un dispositivo
@app.route('/block_device', methods=['POST'])
def block_device():
    mac = request.form['mac_address']  # Cambié 'mac_address' aquí
    try:
        ssh = connect_router()
        block_mac(ssh, mac)
        ssh.close()
        return render_template('index.html', message="Dispositivo bloqueado exitosamente")
    except Exception as e:
        return render_template('index.html', message=f"Error al bloquear dispositivo: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
