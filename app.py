from flask import Flask, render_template, request, redirect, url_for
import subprocess

app = Flask(__name__)

# Función para formatear la MAC al formato Cisco (XXXX.XXXX.XXXX)
def formatear_mac(mac):
    mac = mac.replace(":", "").replace("-", "").lower()
    return '.'.join([mac[i:i+4] for i in range(0, len(mac), 4)])

# Función para ejecutar comandos en el router vía SSH usando subprocess
def bloquear_mac_desde_cli(mac):
    mac = formatear_mac(mac)

    comandos = f"""
config t
class-map match-any unwanted-pc
match source-address mac {mac}
exit
policy-map block
class unwanted-pc
drop
exit
interface FastEthernet1/0
service-policy input block
exit
end
write memory
exit
"""

    ssh_command = (
        "ssh -o HostkeyAlgorithms=ssh-rsa "
        "-o KexAlgorithms=diffie-hellman-group1-sha1 "
        "-o Ciphers=aes128-cbc "
        "-o PreferredAuthentications=password "
        "cisco@192.168.1.1"
    )

    try:
        process = subprocess.Popen(
            ssh_command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        output, error = process.communicate(input=comandos, timeout=20)

        print("=== SALIDA DEL ROUTER ===")
        print(output)
        print("=== ERRORES ===")
        print(error)

        return process.returncode == 0
    except Exception as e:
        print(f"Error al ejecutar SSH: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/block_device', methods=['POST'])
def block_device():
    mac = request.form['mac_address']
    success = bloquear_mac_desde_cli(mac)
    msg = "✅ Dispositivo bloqueado exitosamente" if success else "❌ Error al bloquear la MAC"
    return render_template('index.html', message=msg)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
