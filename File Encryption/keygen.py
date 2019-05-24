from Crypto.PublicKey import RSA
import os


def generateKeys(path, passphrase):
    key = RSA.generate(2048)
    encrypted_key = key.exportKey(passphrase=passphrase, pkcs=8, protection="scryptAndAES128-CBC")

    with open(os.path.join(path, 'private_key.bin'), 'wb') as f:
        f.write(encrypted_key)

    with open(os.path.join(path, 'public_key.bin'), 'wb') as f:
        f.write(key.publickey().exportKey())


if __name__ == "__main__":
    import sys

    assert len(sys.argv) == 3, "You must provide a path where to generate the keys and a pass phrase."
    assert os.path.exists(sys.argv[1]), "Path doesn't exist."
    assert len(sys.argv[2]) >= 8, "Pass phrase too short. Must be 8 characters or longer."

    generateKeys(sys.argv[1], sys.argv[2])
