import pexpect

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

        print("[✓] Conectado al router")

        # 1. Ejecutar show arp
        child.sendline("show arp")
        child.expect("#")
        salida_arp = child.before.decode()

        # 2. Buscar la IP y la INTERFAZ correspondiente a la MAC
        ip_objetivo = None
        interfaz_objetivo = None
        for linea in salida_arp.splitlines():
            if mac_objetivo.lower() in linea.lower():
                partes = linea.split()
                ip_objetivo = partes[1]
                interfaz_objetivo = partes[-1]
                break

        if not ip_objetivo or not interfaz_objetivo:
            print(f"[!] No se encontró IP o interfaz para la MAC {mac_objetivo}")
            child.sendline("exit")
            return

        print(f"[✓] IP detectada para la MAC {mac_objetivo}: {ip_objetivo}")
        print(f"[✓] Interfaz detectada: {interfaz_objetivo}")

        # 3. Configurar ACL para bloquear la IP
        child.sendline("configure terminal")
        child.expect("#")
        child.sendline("no access-list 101")  # Limpia ACL vieja si existe
        child.sendline(f"access-list 101 deny ip host {ip_objetivo} any")
        child.sendline("access-list 101 permit ip any any")

        # 4. Aplicar ACL en la interfaz
        child.sendline(f"interface {interfaz_objetivo}")
        child.sendline("ip access-group 101 in")

        print(f"[✓] Acceso denegado para la IP {ip_objetivo} en la interfaz {interfaz_objetivo}")

        child.sendline("end")
        child.sendline("exit")
        print("[✓] Desconectado")

    except Exception as e:
        print(f"[!] Error durante conexión o ejecución: {e}")

# Ejemplo de uso
bloquear_mac("0800.2788.a0bc")
