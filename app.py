from flask import Flask, render_template, request, redirect, url_for
import pexpect

app = Flask(__name__)

def formatear_mac(mac):
    mac = mac.replace(":", "").replace("-", "").lower()
    return '.'.join([mac[i:i+4] for i in range(0, len(mac), 4)])

def bloquear_mac_con_pexpect(mac):
    mac = formatear_mac(mac)

    comandos = [
        "config t",
        "class-map match-any unwanted-pc",
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
        "write memory",
        "exit"
    ]

    ssh_command = (
        "ssh -o HostkeyAlgorithms=ssh-rsa "
        "-o KexAlgorithms=diffie-hellman-group1-sha1 "
        "-o Ciphers=aes128-cbc "
        "-o PreferredAuthentications=password "
        "cisco@192.168.1.1"
    )

    try:
        child = pexpect.spawn(ssh_command, timeout=30)
        child.expect("password:")
        child.sendline("cisco")  # Aquí pones tu contraseña

        for cmd in comandos:
            child.expect("#")  # Espera el prompt del router
            child.sendline(cmd)

        child.expect("#")
        child.sendline("exit")
        child.close()

        return child.exitstatus == 0
    except Exception as e:
        print(f"Error al bloquear MAC: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/block_device', methods=['POST'])
def block_device():
    mac = request.form['mac_address']
    success = bloquear_mac_con_pexpect(mac)
    msg = "✅ Dispositivo bloqueado exitosamente" if success else "❌ Error al bloquear la MAC"
    return render_template('index.html', message=msg)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
