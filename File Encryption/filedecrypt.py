from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
import os


def decryptFile(filepath, private_key_path, passphrase, outputpath=None):
    with open(filepath, 'rb') as crypt_f:
        private_key = RSA.import_key(open(private_key_path).read(), passphrase=passphrase)

        enc_session_key, nonce, tag, ciphertext = [crypt_f.read(x) for x in (private_key.size_in_bytes(), 16, 16, -1)]
        cipher_rsa = PKCS1_OAEP.new(private_key)
        session_key = cipher_rsa.decrypt(enc_session_key)

        cipher_aes = AES.new(session_key, AES.MODE_EAX, nonce)
        data, name = cipher_aes.decrypt_and_verify(ciphertext, tag).decode().rsplit('&filename=', 1)

        path, rndname = os.path.split(filepath)
        if outputpath: path = outputpath

        with open(os.path.join(path, name), 'w') as f:
            f.write(data)

if __name__ == "__main__":
    import sys

    largv = len(sys.argv)
    assert largv == 4 or largv == 5, "Must provide 'filepath', 'public_key_path', 'passphrase' and optionally 'outputpath'."
    if largv == 5:
        assert os.path.exists(sys.argv[4])

    decryptFile(*sys.argv[1:])
