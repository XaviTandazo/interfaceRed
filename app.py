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
        # Comandos para crear un class-map y un policy-map para bloquear la MAC
        class_map_command = f"""
        class-map match any unwanted-pc's
        match source-address mac {mac}
        """
        
        policy_map_command = f"""
        policy-map block
        class unwanted-pc's
        drop
        """
        
        interface_command = "interface gi 0/1\nservice-policy input block\n"
        
        # Ejecutar los comandos en el router
        ssh.exec_command(f"conf t\n{class_map_command}\n{policy_map_command}\n{interface_command}\nend\n")
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
    mac = request.form['mac']  # Cambié 'mac' aquí
    try:
        ssh = connect_router()
        block_mac(ssh, mac)
        ssh.close()
        return render_template('index.html', message="Dispositivo bloqueado exitosamente")
    except Exception as e:
        return render_template('index.html', message=f"Error al bloquear dispositivo: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
