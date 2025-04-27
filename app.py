from flask import Flask, render_template, request, redirect, url_for
import pexpect
import os
import csv

app = Flask(__name__)

# Ruta donde guardaremos las MACs bloqueadas en formato CSV
BLOCKED_MACS_FILE = os.path.join('static', 'blocked_macs.csv')

# Crear carpeta 'static' si no existe
if not os.path.exists('static'):
    os.makedirs('static')

# Crear el archivo bloqueados si no existe
if not os.path.exists(BLOCKED_MACS_FILE):
    with open(BLOCKED_MACS_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["MAC Address", "IP Address"])

# Función para bloquear una MAC
def bloquear_mac(mac_objetivo):
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
        mac_objetivo_formateada = mac_objetivo.replace(":", ".").lower()  # Formateamos la MAC a formato Cisco
        for linea in salida_arp.splitlines():
            if mac_objetivo_formateada in linea.lower():
                partes = linea.split()
                ip_objetivo = partes[1]
                break

        if not ip_objetivo:
            child.sendline("exit")
            return f"No se encontró IP para la MAC {mac_objetivo}"

        # Registrar la MAC y su IP asociada en el archivo CSV
        with open(BLOCKED_MACS_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([mac_objetivo, ip_objetivo])

        # Bloquear la MAC en la red (usando la IP)
        child.sendline("configure terminal")
        child.expect("#")
        child.sendline(f"ip access-list extended BLOCK_MAC")
        child.sendline(f"deny ip host {ip_objetivo} any")
        child.sendline("permit ip any any")
        child.sendline("end")
        child.sendline("exit")

        return f"MAC {mac_objetivo} bloqueada correctamente."

    except Exception as e:
        return f"Error al bloquear MAC: {e}"

# Función para permitir una MAC (eliminando el bloqueo)
def permitir_mac(mac_objetivo):
    try:
        # Obtener IP asociada a la MAC desde el archivo CSV
        ip_objetivo = None
        with open(BLOCKED_MACS_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if row[0].lower() == mac_objetivo.lower():
                    ip_objetivo = row[1]
                    break

        if not ip_objetivo:
            return f"No se encontró la IP asociada a la MAC {mac_objetivo}"

        comando_ssh = (
            "ssh -o HostkeyAlgorithms=ssh-rsa "
            "-o KexAlgorithms=diffie-hellman-group1-sha1 "
            "-o Ciphers=aes128-cbc "
            "-o PreferredAuthentications=password cisco@192.168.1.1"
        )
        child = pexpect.spawn(comando_ssh, timeout=20)
        child.expect("password:")
        child.sendline("cisco")
        child.expect("#")

        # Eliminar la regla de bloqueo para esa IP
        child.sendline("configure terminal")
        child.expect("#")
        child.sendline(f"no ip access-list extended BLOCK_MAC")
        child.sendline("end")
        child.sendline("exit")

        # Eliminar la MAC y su IP asociada del archivo CSV
        with open(BLOCKED_MACS_FILE, 'r', newline='') as f:
            rows = list(csv.reader(f))
        with open(BLOCKED_MACS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            for row in rows:
                if row[0].lower() != mac_objetivo.lower():
                    writer.writerow(row)

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
    message = bloquear_mac(mac_address)
    return render_template('index.html', message=message)

@app.route('/allow_device', methods=['POST'])
def allow_device():
    mac_address = request.form['mac_address']
    message = permitir_mac(mac_address)
    return render_template('index.html', message=message)

@app.route('/blocked_list', methods=['GET'])
def blocked_list():
    blocked_macs = []
    if os.path.exists(BLOCKED_MACS_FILE):
        with open(BLOCKED_MACS_FILE, 'r', newline='') as f:
            reader = csv.reader(f)
            next(reader)  # Saltar el encabezado
            for row in reader:
                blocked_macs.append(f"MAC: {row[0]} - IP: {row[1]}")
    message = "Dispositivos bloqueados: " + (", ".join(blocked_macs) if blocked_macs else "Ninguno")
    return render_template('index.html', message=message)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
