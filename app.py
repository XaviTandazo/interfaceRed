from flask import Flask, render_template, request, redirect, url_for
import pexpect
import os

app = Flask(__name__)

# Ruta donde guardaremos las MACs bloqueadas
BLOCKED_MACS_FILE = os.path.join('static', 'blocked_macs.txt')

# Crear carpeta 'static' si no existe
if not os.path.exists('static'):
    os.makedirs('static')

# Crear el archivo bloqueados si no existe
if not os.path.exists(BLOCKED_MACS_FILE):
    with open(BLOCKED_MACS_FILE, 'w') as f:
        pass

# Función para bloquear una MAC (apagando la interfaz)
def bloquear_mac_apagando_interfaz(mac_objetivo):
    comando_ssh = (
        "ssh -o HostkeyAlgorithms=ssh-rsa "
        "-o KexAlgorithms=diffie-hellman-group1-sha1 "
        "-o Ciphers=aes128-cbc "
        "-o PreferredAuthentications=password cisco@192.168.1.1"
    )
    try:
        child = pexpect.spawn(comando_ssh, timeout=20)
        child.expect("password:")
        child.sendline("cisco")
        child.expect("#")

        child.sendline("show arp")
        child.expect("#")
        salida_arp = child.before.decode()

        ip_objetivo = None
        interfaz_objetivo = None
        for linea in salida_arp.splitlines():
            if mac_objetivo.lower() in linea.lower():
                partes = linea.split()
                ip_objetivo = partes[1]
                interfaz_objetivo = partes[-1]
                break

        if not ip_objetivo or not interfaz_objetivo:
            child.sendline("exit")
            return f"No se encontró IP o interfaz para la MAC {mac_objetivo}"

        child.sendline("configure terminal")
        child.expect("#")
        child.sendline(f"interface {interfaz_objetivo}")
        child.sendline("shutdown")

        child.sendline("end")
        child.sendline("exit")

        # Registrar la MAC como bloqueada
        with open(BLOCKED_MACS_FILE, 'a') as f:
            f.write(mac_objetivo + '\n')

        return f"MAC {mac_objetivo} bloqueada correctamente."

    except Exception as e:
        return f"Error al bloquear MAC: {e}"

# Función para permitir una MAC (encender la interfaz)
def permitir_mac_encendiendo_interfaz(mac_objetivo):
    comando_ssh = (
        "ssh -o HostkeyAlgorithms=ssh-rsa "
        "-o KexAlgorithms=diffie-hellman-group1-sha1 "
        "-o Ciphers=aes128-cbc "
        "-o PreferredAuthentications=password cisco@192.168.1.1"
    )
    try:
        child = pexpect.spawn(comando_ssh, timeout=20)
        child.expect("password:")
        child.sendline("cisco")
        child.expect("#")

        child.sendline("show arp")
        child.expect("#")
        salida_arp = child.before.decode()

        ip_objetivo = None
        interfaz_objetivo = None
        for linea in salida_arp.splitlines():
            if mac_objetivo.lower() in linea.lower():
                partes = linea.split()
                ip_objetivo = partes[1]
                interfaz_objetivo = partes[-1]
                break

        if not ip_objetivo or not interfaz_objetivo:
            child.sendline("exit")
            return f"No se encontró IP o interfaz para la MAC {mac_objetivo}"

        child.sendline("configure terminal")
        child.expect("#")
        child.sendline(f"interface {interfaz_objetivo}")
        child.sendline("no shutdown")

        child.sendline("end")
        child.sendline("exit")

        # Quitar la MAC de la lista de bloqueados
        if os.path.exists(BLOCKED_MACS_FILE):
            with open(BLOCKED_MACS_FILE, 'r') as f:
                macs = f.readlines()
            macs = [mac.strip() for mac in macs if mac.strip() != mac_objetivo]
            with open(BLOCKED_MACS_FILE, 'w') as f:
                for mac in macs:
                    f.write(mac + '\n')

        return f"MAC {mac_objetivo} permitida correctamente."

    except Exception as e:
        return f"Error al permitir MAC: {e}"

# Rutas Flask

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/block_device', methods=['POST'])
def block_device():
    mac_address = request.form['mac_address']
    message = bloquear_mac_apagando_interfaz(mac_address)
    return render_template('index.html', message=message)

@app.route('/allow_device', methods=['POST'])
def allow_device():
    mac_address = request.form['mac_address']
    message = permitir_mac_encendiendo_interfaz(mac_address)
    return render_template('index.html', message=message)

@app.route('/blocked_list', methods=['GET'])
def blocked_list():
    if os.path.exists(BLOCKED_MACS_FILE):
        with open(BLOCKED_MACS_FILE, 'r') as f:
            macs = f.readlines()
        macs = [mac.strip() for mac in macs if mac.strip()]
    else:
        macs = []

    message = "MACs bloqueadas: " + (", ".join(macs) if macs else "Ninguna")
    return render_template('index.html', message=message)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
