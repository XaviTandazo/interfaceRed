import pexpect

def conectar_al_router():
    ssh_command = (
        "ssh -o HostkeyAlgorithms=ssh-rsa "
        "-o KexAlgorithms=diffie-hellman-group1-sha1 "
        "-o Ciphers=aes128-cbc "
        "-o PreferredAuthentications=password "
        "cisco@192.168.1.1"
    )

    try:
        child = pexpect.spawn(ssh_command, timeout=20)
        child.logfile = open("ssh_log.txt", "wb")  # Guarda todo lo que ocurre en un log

        # Esperar el prompt de contraseña
        child.expect("password:")
        child.sendline("cisco")  # Cambia esto si tu contraseña es distinta

        # Esperar el prompt del router (ej: R1>)
        child.expect(">")
        child.sendline("enable")

        # Esperar el prompt del modo enable (ej: R1#)
        child.expect("#")
        child.sendline("config t")

        # Esperar que entremos a configuración global (ej: R1(config)#)
        child.expect("(config)#")
        print("✅ Conexión y entrada a modo de configuración exitosa.")
        child.sendline("exit")
        child.sendline("exit")
        child.sendline("exit")
        child.close()

    except pexpect.exceptions.TIMEOUT:
        print("❌ Tiempo de espera agotado.")
    except pexpect.exceptions.EOF:
        print("❌ Conexión terminada inesperadamente.")
    except Exception as e:
        print(f"❌ Error general: {e}")

conectar_al_router()
