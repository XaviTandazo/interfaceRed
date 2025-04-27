from flask import Flask, render_template, request
import pexpect
import os
import csv

app = Flask(__name__)

# Ruta donde guardaremos las MACs bloqueadas
BLOCKED_MACS_FILE = os.path.join('static', 'blocked_macs.csv')

# Crear carpeta 'static' si no existe
if not os.path.exists('static'):
    os.makedirs('static')

# Crear el archivo bloqueados si no existe
if not os.path.exists(BLOCKED_MACS_FILE):
    with open(BLOCKED_MACS_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['mac_address', 'ip_address'])

# Función para bloquear tráfico de una IP asociada a la MAC
def bloquear_trafico_ip(ip_objetivo):
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

        child.sendline("configure terminal")
        child.expect("#")

        # Configurar acceso controlado para bloquear tráfico de la IP
        child.sendline(f"ip access-list extended BLOCK_TRAFFIC_{ip_objetivo}")
        child.sendline(f"deny ip {ip_objetivo} 0.0.0.255 any")
        child.sendline("permit ip any any")
        child.sendline("exit")

        # Consultar la interfaz a la que está conectada la IP
        interfaz = consultar_interfaz_ip(ip_objetivo)
        if interfaz:
            # Aplicar el ACL (Access Control List) a la interfaz correspondiente
            child.sendline(f"interface {interfaz}")
            child.sendline(f"ip access-group BLOCK_TRAFFIC_{ip_objetivo} in")
            child.sendline("end")

            child.sendline("exit")

            # Registrar la MAC y la IP en el archivo de MACs bloqueadas
            with open(BLOCKED_MACS_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([mac_objetivo, ip_objetivo])

            return f"Tráfico de la IP {ip_objetivo} bloqueado correctamente en la interfaz {interfaz}."
        else:
            return f"No se encontró la interfaz para la IP {ip_objetivo}."

    except Exception as e:
        return f"Error al bloquear tráfico: {e}"

# Función para permitir el tráfico de una IP asociada a la MAC
def permitir_trafico_ip(ip_objetivo):
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

        child.sendline("configure terminal")
        child.expect("#")

        # Eliminar ACL que bloquea la IP
        child.sendline(f"no ip access-list extended BLOCK_TRAFFIC_{ip_objetivo}")
        child.sendline("exit")

        child.sendline("exit")

        # Eliminar la IP de la lista de bloqueadas
        if os.path.exists(BLOCKED_MACS_FILE):
            with open(BLOCKED_MACS_FILE, 'r') as f:
                reader = csv.reader(f)
                macs = list(reader)

            macs = [m for m in macs if m[1] != ip_objetivo]

            with open(BLOCKED_MACS_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(macs)

        return f"Tráfico de la IP {ip_objetivo} permitido nuevamente."

    except Exception as e:
        return f"Error al permitir tráfico: {e}"

# Función para consultar la IP asociada a la MAC
def consultar_ip_mac(mac_objetivo):
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

        for linea in salida_arp.splitlines():
            if mac_objetivo.lower() in linea.lower():
                partes = linea.split()
                return partes[1]  # La IP está en la segunda columna

        return None

    except Exception as e:
        return None

# Función para consultar la interfaz a la que está conectada una IP
def consultar_interfaz_ip(ip_objetivo):
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

        child.sendline("show ip interface brief")
        child.expect("#")
        salida_interfaces = child.before.decode()

        for linea in salida_interfaces.splitlines():
            if ip_objetivo in linea:
                # Dividir la línea y encontrar la interfaz
                partes = linea.split()
                return partes[0]  # La interfaz está en la primera columna

        return None

    except Exception as e:
        return None

# Rutas Flask
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/block_device', methods=['POST'])
def block_device():
    mac_address = request.form['mac_address']
    # Consultar la IP asociada a la MAC
    ip_objetivo = consultar_ip_mac(mac_address)
    if ip_objetivo:
        message = bloquear_trafico_ip(ip_objetivo)
    else:
        message = f"No se encontró la IP asociada a la MAC {mac_address}"
    return render_template('index.html', message=message)

@app.route('/allow_device', methods=['POST'])
def allow_device():
    mac_address = request.form['mac_address']
    # Consultar la IP asociada a la MAC
    ip_objetivo = consultar_ip_mac(mac_address)
    if ip_objetivo:
        message = permitir_trafico_ip(ip_objetivo)
    else:
        message = f"No se encontró la IP asociada a la MAC {mac_address}"
    return render_template('index.html', message=message)

@app.route('/blocked_list', methods=['GET'])
def blocked_list():
    if os.path.exists(BLOCKED_MACS_FILE):
        with open(BLOCKED_MACS_FILE, 'r') as f:
            reader = csv.reader(f)
            macs = list(reader)[1:]  # Omitir el encabezado

        message = "MACs bloqueadas: " + (", ".join([f"{mac[0]} - {mac[1]}" for mac in macs]) if macs else "Ninguna")
    else:
        message = "No se ha encontrado el archivo de MACs bloqueadas."

    return render_template('index.html', message=message)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
