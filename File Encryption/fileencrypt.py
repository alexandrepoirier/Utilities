from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
import os
import random

session_history = []
ascii_list = [i for i in range(65, 91)]
ascii_list.extend([i for i in range(97, 123)])

def randomString():
    global session_history

    rndstr = ""
    for i in range(16):
        if i % random.randint(1,2) == 0:
            rndstr += chr(random.choice(ascii_list))
        else:
            rndstr += str(random.randint(0, 9))

    if rndstr in session_history:
        rndstr = randomString()
    else:
        session_history.append(rndstr)

    return rndstr

def encryptFile(filepath, public_key_path, outputpath=None):
    with open(filepath, 'r') as in_file:
        path, name = os.path.split(filepath)

        if outputpath: path = outputpath
        rndname = "{}.bin".format(randomString())
        with open(os.path.join(path, rndname), 'wb') as out_file:
            recipient_key = RSA.import_key(open(public_key_path).read())
            session_key = get_random_bytes(16)

            cipher_rsa = PKCS1_OAEP.new(recipient_key)
            out_file.write(cipher_rsa.encrypt(session_key))

            cipher_aes = AES.new(session_key, AES.MODE_EAX)
            try:
                data = in_file.read() + "&filename={}".format(name)
            except UnicodeDecodeError:
                print("[Warning] Encountered UnicodeDecodeError while parsing file {}".format(filepath))
                return os.path.join(path, rndname)

            ciphertext, tag = cipher_aes.encrypt_and_digest(data.encode())

            [out_file.write(x) for x in (cipher_aes.nonce, tag, ciphertext)]

    return 0


if __name__ == "__main__":
    import sys

    largv = len(sys.argv)
    assert largv == 3 or largv == 4, "Must provide 'filepath', 'public_key_path' and optionally 'outputpath'."
    if largv == 4:
        assert os.path.exists(sys.argv[3])

    encryptFile(*sys.argv[1:])
