---
layout: activity
title: "Activity 9 — Public-Key Cryptography with PyCryptodome"
activity_id: 9
activity_title: "Public-Key Cryptography with PyCryptodome"
course: "CSCE 313 · Introduction to Computer Systems"
term: "Fall 2026"
relates_to: "Security"
duration: "30 minutes"
published: false     # held until release; the page 404s until this is removed
listed: false        # reachable by direct link, not shown in the index
description: "Make an RSA key pair with PyCryptodome, then use it the two ways public-key cryptography is used: encrypt a message with the public key and decrypt it with the private key, and sign a message with the private key and verify it with the public key."
---

<nav class="toc" aria-labelledby="toc-heading" markdown="1">
## On this page
{: #toc-heading .toc__heading .no_toc}

1. TOC
{:toc}
</nav>

## 1. Description

A public-key system gives you **two keys that go together**: a **private key**
you keep secret, and a **public key** you can hand to anyone. What one key does,
only the other can undo. That one idea gives you the two things security is
built on:

- **Encryption (keeping a message private).** Anyone encrypts a message with
  your **public** key, and only you can read it, with your **private** key.
- **Signing (proving who sent a message).** You sign a message with your
  **private** key, and anyone can check it came from you, with your **public**
  key.

You will write five short programs with **PyCryptodome**, Python's cryptography
library, one for each step:

| Program | Uses | Does |
|---|---|---|
| `keygen.py` | — | makes the key pair → `private.pem`, `public.pem` |
| `encrypt.py` | **public** key | encrypts a message → `message.enc` |
| `decrypt.py` | **private** key | reads `message.enc` back |
| `sign.py` | **private** key | signs a message → `signature.bin` |
| `verify.py` | **public** key | checks the signature |

Everything runs as yourself — no `sudo`, no network. The message is the same
throughout: `b"Transfer $100 to Alice"`.

## 2. Getting Your Repository

Accept the assignment, then clone your own copy:

<https://classroom50.org/CSCE-313-FA26/csce-313-fa26/assignments/activity-9/accept>

```bash
git clone https://github.com/CSCE-313-FA26/csce-313-fa26-activity-9-<your-username>.git
cd csce-313-fa26-activity-9-<your-username>
```

PyCryptodome may already be installed. Check with:

```bash
python3 -c "import Crypto; print(Crypto.__version__)"
```

If that prints a version number you are set. If it says
`ModuleNotFoundError: No module named 'Crypto'`, install it for yourself (no
root needed):

```bash
pip install --user pycryptodome
```

> **The pip name and the import name are different.** You install
> **`pycryptodome`** but you `import Crypto`. That is normal for this library.

The repo ships the five programs, each with a line or two to finish.

## 3. Task 1 — make a key pair (`keygen.py`)

`RSA.generate(2048)` makes one 2048-bit key object that holds **both** halves.
You save each half to its own file. Finish the three TODOs:

```python
from Crypto.PublicKey import RSA

# Make one 2048-bit RSA key pair.
key = RSA.generate(2048)

# The PRIVATE key - keep it secret. Save it to private.pem.
private_pem = key.export_key()
f = open("private.pem", "wb")
f.write(private_pem)
f.close()

# The PUBLIC key - safe to share. Save it to public.pem.
public_key = key.publickey()
public_pem = public_key.export_key()
f = open("public.pem", "wb")
f.write(public_pem)
f.close()

print("wrote private.pem and public.pem")
```

Run it and look at what you made:

```bash
$ python3 keygen.py
wrote private.pem and public.pem
$ head -1 private.pem
-----BEGIN RSA PRIVATE KEY-----
$ head -1 public.pem
-----BEGIN PUBLIC KEY-----
```

> **Open the files in `wb` mode.** `export_key()` returns raw **bytes**, so the
> file is opened `"wb"` (write-binary), not `"w"`. The same is true every time
> you save a key, a ciphertext, or a signature in this activity.

## 4. Task 2 — encrypt with the public key (`encrypt.py`)

To keep a message private, you encrypt it with the **public** key, using the
`PKCS1_OAEP` scheme. Finish the two TODOs:

```python
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

message = b"Transfer $100 to Alice"

# Load the public key.
public_key = RSA.import_key(open("public.pem").read())

# Make a cipher from the public key and encrypt the message.
cipher = PKCS1_OAEP.new(public_key)
ciphertext = cipher.encrypt(message)

# Save the ciphertext to message.enc.
f = open("message.enc", "wb")
f.write(ciphertext)
f.close()

print("encrypted", len(message), "bytes into message.enc")
```

The ciphertext is 256 bytes of noise — the whole point is that it looks like
nothing:

```bash
$ python3 encrypt.py
encrypted 22 bytes into message.enc
$ wc -c message.enc
256 message.enc
```

## 5. Task 3 — decrypt with the private key (`decrypt.py`)

Only the **private** key can undo it. Finish the two TODOs:

```python
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

# Load the private key.
private_key = RSA.import_key(open("private.pem").read())

# Read the ciphertext encrypt.py wrote.
ciphertext = open("message.enc", "rb").read()

# Make a cipher from the private key and decrypt.
cipher = PKCS1_OAEP.new(private_key)
message = cipher.decrypt(ciphertext)

print("decrypted message:", message)
```

```bash
$ python3 decrypt.py
decrypted message: b'Transfer $100 to Alice'
```

The message comes back exactly. (It prints with a `b` in front because it is
bytes — that is fine.)

## 6. Task 4 — sign with the private key (`sign.py`)

A signature proves the message came from the private-key holder and was not
changed. You **hash** the message first (so the signature is a fixed size), then
sign the hash with the **private** key. Finish the two TODOs:

```python
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

message = b"Transfer $100 to Alice"

# Load the private key.
private_key = RSA.import_key(open("private.pem").read())

# Hash the message, then sign the hash.
digest = SHA256.new(message)
signature = pkcs1_15.new(private_key).sign(digest)

# Save the signature to signature.bin.
f = open("signature.bin", "wb")
f.write(signature)
f.close()

print("wrote signature.bin")
```

```bash
$ python3 sign.py
wrote signature.bin
$ wc -c signature.bin
256 signature.bin
```

## 7. Task 5 — verify with the public key (`verify.py`)

Anyone with the **public** key can check the signature. `verify()` returns
quietly when the signature is good and **raises an error** when it is not, so you
wrap it in `try` / `except` and print the result. Finish the one TODO:

```python
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

message = b"Transfer $100 to Alice"

# Load the public key.
public_key = RSA.import_key(open("public.pem").read())

# Read the signature sign.py wrote.
signature = open("signature.bin", "rb").read()

# Hash the message the same way the signer did, then check the signature.
digest = SHA256.new(message)
try:
    pkcs1_15.new(public_key).verify(digest, signature)
    print("signature is valid")
except (ValueError, TypeError):
    print("signature is NOT valid")
```

```bash
$ python3 verify.py
signature is valid
```

> **Prove it really checks.** Change one character of `message` in `verify.py`
> and run it again — it now prints `signature is NOT valid`, because the hash no
> longer matches what was signed. Change it back when you are done.

## 8. Run it all together

The five programs form one pipeline. Run them in order:

```bash
$ python3 keygen.py
wrote private.pem and public.pem
$ python3 encrypt.py
encrypted 22 bytes into message.enc
$ python3 decrypt.py
decrypted message: b'Transfer $100 to Alice'
$ python3 sign.py
wrote signature.bin
$ python3 verify.py
signature is valid
```

That is the whole shape of public-key cryptography: the public key encrypts and
verifies, the private key decrypts and signs.

## 9. Checking Your Work

Run the grader yourself before you push — it is the same one that runs on the
server:

```bash
make test
```

Each of the five programs is graded on **what it produces** — a valid key pair,
a ciphertext the private key can recover, a printed message, a signature the
public key accepts. The grader uses its **own** key pair for the four programs
after `keygen.py`, so each task is graded on its own: a mistake in one does not
hide the others. Everything is root-free, so `make test` works as yourself.

## 10. How It Is Graded

Nothing reads your source for credit. Extra fields or different variable names
do not matter — only what each program does.

| Row | Points |
|---|---|
| `keygen.py` writes a valid 2048-bit RSA key pair | 20 |
| `encrypt.py` encrypts the message with the public key | 20 |
| `decrypt.py` recovers a message with the private key | 20 |
| `sign.py` signs the message with the private key | 20 |
| `verify.py` accepts a good signature and rejects a bad one | 20 |

## 11. Submitting

```bash
git add keygen.py encrypt.py decrypt.py sign.py verify.py
git commit -m "Activity 9"
git push
```

Push as often as you like; every push is graded and the last one counts.

## 12. If You Finish Early

Each is a few lines, none is graded.

- **Sign a file instead of a line.** Read a file's bytes
  (`open("notes.txt","rb").read()`), hash those, and sign the hash. This is how
  real software releases are signed.
- **Watch encryption fail at the size limit.** RSA-OAEP on a 2048-bit key can
  encrypt at most 214 bytes. Try encrypting a longer `message` (say `b"A" * 215`)
  and read the error — it is why real systems encrypt a short random key with RSA
  and the bulk of the data with that key.
- **Swap the keys on purpose.** Try to decrypt `message.enc` with the *public*
  key, or verify against the *wrong* public key, and see exactly how each fails.
- **Compare two signatures.** Sign the same message twice and compare the two
  `signature.bin` files with `cmp` — `pkcs1_15` is deterministic, so they match.
  Then encrypt the same message twice and compare — `PKCS1_OAEP` adds randomness,
  so they differ every time.
