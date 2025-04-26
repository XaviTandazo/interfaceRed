def conectar_ssh():
    comando_ssh = (
        "ssh -o HostkeyAlgorithms=ssh-rsa "
        "-o KexAlgorithms=diffie-hellman-group1-sha1 "
        "-o Ciphers=aes128-cbc "
        "-o PreferredAuthentications=password "
        "cisco@192.168.1.1"
    )

    try:
        # Inicia la conexión SSH
        child = pexpect.spawn(comando_ssh, timeout=20)
        child.expect("password:")
        child.sendline("cisco")

        # Espera hasta que se muestre el prompt del router (ej. R1#)
        child.expect("#")
        print("✅ Conexión exitosa. Estás en el prompt del router.")

        # Aquí podrías seguir enviando comandos si deseas
        # Ejemplo: child.sendline("show version")

        # Finaliza la sesión
        child.sendline("exit")
        child.close()

    except pexpect.exceptions.TIMEOUT:
        print("❌ Tiempo agotado. Verifica la conexión.")
    except pexpect.exceptions.EOF:
        print("❌ Conexión cerrada inesperadamente.")
    except Exception as e:
        print(f"❌ Error: {e}")

conectar_ssh()