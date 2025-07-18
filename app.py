from flask import Flask, render_template, request
import pexpect
import os
import csv

app = Flask(__name__)

# Archivos
BLOCKED_MACS_FILE = os.path.join('static', 'blocked_macs.csv')
INTERFACES_IPS_FILE = os.path.join('static', 'interfaces_ips.csv')

# Asegurar carpetas/archivos
os.makedirs('static', exist_ok=True)

for file in [BLOCKED_MACS_FILE, INTERFACES_IPS_FILE]:
    if not os.path.exists(file):
        with open(file, mode='w', newline='') as f:
            writer = csv.writer(f)
            if 'blocked_macs' in file:
                writer.writerow(['mac_address', 'ip_address'])
            else:
                writer.writerow(['interface', 'ip_address'])

# Función SSH para conectarse
def crear_conexion_ssh():
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
    return child

# Función para actualizar la lista de interfaces e IPs
def actualizar_interfaces_ips():
    try:
        child = crear_conexion_ssh()
        child.sendline("show ip interface brief")
        child.expect("#")
        salida = child.before.decode()

        interfaces = []
        lines = salida.splitlines()

        # Saltamos las primeras dos líneas (cabecera) y procesamos desde la línea 3
        for linea in lines[2:]:
            if not linea.strip():  # Saltamos las líneas vacías
                continue

            # Eliminamos espacios extra al inicio y final de la línea
            linea = linea.strip()

            # Buscamos el primer espacio para extraer la interfaz
            partes = linea.split()

            # Verificamos que haya al menos dos partes: interfaz y IP
            if len(partes) >= 2:
                interfaz = partes[0]
                ip = partes[1] if partes[1] != "unassigned" else "unassigned"

                # Guardamos la interfaz y la IP en la lista
                interfaces.append((interfaz, ip))

        # Guardamos las interfaces y IPs en el archivo
        with open(INTERFACES_IPS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['interface', 'ip_address'])
            writer.writerows(interfaces)

        child.sendline("exit")
    except Exception as e:
        print(f"Error actualizando interfaces: {e}")


# Función para buscar la interfaz correspondiente a una IP
def encontrar_interfaz_por_ip(ip_objetivo):
    if not os.path.exists(INTERFACES_IPS_FILE):
        actualizar_interfaces_ips()

    with open(INTERFACES_IPS_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for fila in reader:
            ip_base = fila['ip_address']
            if ip_base != "unassigned" and ip_objetivo.startswith(ip_base.rsplit('.', 1)[0]):
                return fila['interface']
    return None

# Función para bloquear tráfico de una IP
def bloquear_trafico_ip(mac_objetivo, ip_objetivo):
    try:
        child = crear_conexion_ssh()

        # Entra en modo de configuración global
        child.sendline("configure terminal")
        child.expect("#")

        # Verifica si ACL 100 ya existe, si no, la crea
        child.sendline("show access-lists")
        child.expect("#")
        salida = child.before.decode()

        if "100" not in salida:
            child.sendline("ip access-list extended 100")
            child.expect("#")
            child.sendline(f"deny ip host {ip_objetivo} any")
            child.sendline("permit ip any any")
            child.sendline("exit")
            child.expect("#")
        
        # Encuentra la interfaz correcta para la IP objetivo
        interfaz = encontrar_interfaz_por_ip(ip_objetivo)
        if interfaz:
            child.sendline(f"interface {interfaz}")
            child.sendline("ip access-group 100 in")
            child.sendline("exit")
            child.expect("#")
        else:
            return f"No se encontró la interfaz para la IP {ip_objetivo}."

        # Aplica los cambios y termina la sesión
        child.sendline("end")
        child.sendline("exit")
        child.expect("#")

        # Registrar MAC e IP bloqueadas
        with open(BLOCKED_MACS_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([mac_objetivo, ip_objetivo])

        return f"Tráfico de {ip_objetivo} bloqueado en {interfaz}."
    except Exception as e:
        return f"Error al bloquear tráfico: {e}"

# Función para permitir tráfico (eliminar la regla de bloqueo)
def permitir_trafico_ip(mac_objetivo, ip_objetivo):
    try:
        child = crear_conexion_ssh()

        child.sendline("configure terminal")
        child.expect("#")

        child.sendline("no ip access-list extended 100")
        child.sendline("ip access-list extended 100")
        child.sendline("permit ip any any")
        child.sendline("exit")

        child.sendline("end")
        child.sendline("exit")

        # Quitar de archivo bloqueados
        if os.path.exists(BLOCKED_MACS_FILE):
            with open(BLOCKED_MACS_FILE, 'r') as f:
                reader = csv.reader(f)
                macs = list(reader)

            macs = [m for m in macs if m[1] != ip_objetivo]

            with open(BLOCKED_MACS_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(macs)

        return f"Tráfico de {ip_objetivo} permitido."
    except Exception as e:
        return f"Error al permitir tráfico: {e}"

# Función para consultar IP desde MAC
def consultar_ip_mac(mac_objetivo):
    try:
        child = crear_conexion_ssh()
        child.sendline("show arp")
        child.expect("#")
        salida = child.before.decode()

        for linea in salida.splitlines():
            if mac_objetivo.lower() in linea.lower():
                partes = linea.split()
                return partes[1]  # Segunda columna: IP

        child.sendline("exit")
        return None
    except Exception as e:
        print(f"Error consultando ARP: {e}")
        return None

# FLASK - Rutas

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/block_device', methods=['POST'])
def block_device():
    mac_address = request.form['mac_address']
    ip_objetivo = consultar_ip_mac(mac_address)
    if ip_objetivo:
        message = bloquear_trafico_ip(mac_address, ip_objetivo)
    else:
        message = f"No se encontró IP para MAC {mac_address}"
    return render_template('index.html', message=message)

@app.route('/allow_device', methods=['POST'])
def allow_device():
    mac_address = request.form['mac_address']
    ip_objetivo = consultar_ip_mac(mac_address)
    if ip_objetivo:
        message = permitir_trafico_ip(mac_address, ip_objetivo)
    else:
        message = f"No se encontró IP para MAC {mac_address}"
    return render_template('index.html', message=message)

@app.route('/blocked_list', methods=['GET'])
def blocked_list():
    if os.path.exists(BLOCKED_MACS_FILE):
        with open(BLOCKED_MACS_FILE, 'r') as f:
            reader = csv.reader(f)
            macs = list(reader)[1:]
        message = "MACs bloqueadas: " + (", ".join([f"{m[0]} - {m[1]}" for m in macs]) if macs else "Ninguna")
    else:
        message = "No hay dispositivos bloqueados."
    return render_template('index.html', message=message)

if __name__ == "__main__":
    actualizar_interfaces_ips()  # Actualizamos interfaces al inicio
    app.run(host='0.0.0.0', port=5000, debug=True)
