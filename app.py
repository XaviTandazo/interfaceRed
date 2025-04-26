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

        print("[✓] Conectado al router")

        # 1. Ejecutar show arp
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

        if not interfaz_objetivo:
            print("[!] No se encontró en ARP, buscando interfaces administrativamente down...")

            # 2. Buscar interfaces DOWN
            child.sendline("show ip interface brief")
            child.expect("#")
            salida_interfaces = child.before.decode()

            interfaces_down = []
            for linea in salida_interfaces.splitlines():
                if "administratively down" in linea.lower():
                    partes = linea.split()
                    nombre_interfaz = partes[0]
                    # Solo considerar interfaces Ethernet
                    if nombre_interfaz.startswith("FastEthernet") or nombre_interfaz.startswith("GigabitEthernet"):
                        interfaces_down.append(nombre_interfaz)

            if not interfaces_down:
                print("[!] No hay interfaces FastEthernet/GigabitEthernet apagadas. Nada que hacer.")
                child.sendline("exit")
                return

            print(f"[✓] Interfaces Ethernet apagadas encontradas: {interfaces_down}")
            
            # Tomamos la primera (en este caso sería FastEthernet1/0)
            interfaz_objetivo = interfaces_down[0]

        # 3. Encender la interfaz
        child.sendline("configure terminal")
        child.expect("#")
        child.sendline(f"interface {interfaz_objetivo}")
        child.sendline("no shutdown")
        print(f"[✓] Interfaz {interfaz_objetivo} encendida")

        # 4. Eliminar MAC del archivo bloqueado
        if os.path.exists(BLOCKED_MACS_FILE):
            with open(BLOCKED_MACS_FILE, 'r') as f:
                macs = f.read().splitlines()
            macs = [m for m in macs if m.lower() != mac_objetivo.lower()]
            with open(BLOCKED_MACS_FILE, 'w') as f:
                f.write('\n'.join(macs))
            print(f"[✓] MAC {mac_objetivo} eliminada de la lista bloqueada")

        child.sendline("end")
        child.sendline("exit")
        print("[✓] Desconectado")

    except Exception as e:
        print(f"[!] Error durante conexión o ejecución: {e}")

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
