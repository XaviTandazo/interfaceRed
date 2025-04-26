import pexpect

# Comando SSH para conectar al router
comando_ssh = "ssh -o HostkeyAlgorithms=ssh-rsa -o KexAlgorithms=diffie-hellman-group1-sha1 -o Ciphers=aes128-cbc -o PreferredAuthentications=password cisco@192.168.1.1"

# Dirección MAC del dispositivo (cambiar según el dispositivo)
mac_address = "0800.27a7.8f04"

# Dirección IP del dispositivo (cambiar según lo obtenido)
ip_address = "192.168.1.10"

# Conectar al router
child = pexpect.spawn(comando_ssh, timeout=20)

# Ingresar la contraseña
child.expect("Password:")
child.sendline("cisco")  # Cambiar la contraseña si es necesario

# Esperar al prompt del router
child.expect("R3725#")

# Buscar la IP en la tabla ARP
child.sendline("show ip arp")
child.expect("R3725#")

# Comprobar si la IP está presente en la salida
if ip_address in child.before.decode('utf-8'):
    print(f"Dispositivo con IP {ip_address} detectado. Apagando la interfaz...")
    
    # Apagar la interfaz
    child.sendline("configure terminal")
    child.expect("R3725(config)#")
    child.sendline(f"interface FastEthernet0/1")
    child.expect("R3725(config-if)#")
    child.sendline("shutdown")
    child.expect("R3725(config-if)#")
    
    print(f"Interfaz FastEthernet0/1 apagada para el dispositivo con IP {ip_address}.")
else:
    print(f"No se detectó el dispositivo con IP {ip_address}.")
