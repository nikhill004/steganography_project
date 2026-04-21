"""
encrypt.py - Dual encryption layer
Implements Caesar Cipher followed by Vigenere Cipher.

Paper reference:
  "Improved Message Payload and Security of Image Steganography
   using 3-3-2 LSB and Dual Encryption"
"""


# ---------------------------------------------------------------------------
# Caesar Cipher
# ---------------------------------------------------------------------------

def caesar_encrypt(plaintext: str, shift: int) -> str:
    """
    Encrypt *plaintext* using Caesar Cipher with the given *shift*.

    - Uppercase letters are shifted within A-Z.
    - Lowercase letters are shifted within a-z.
    - Non-alphabetic characters are left unchanged.

    Parameters
    ----------
    plaintext : str
    shift     : int  (positive = right shift, negative = left shift)

    Returns
    -------
    str  ciphertext
    """
    result = []
    for ch in plaintext:
        if ch.isupper():
            shifted = (ord(ch) - ord('A') + shift) % 26
            result.append(chr(shifted + ord('A')))
        elif ch.islower():
            shifted = (ord(ch) - ord('a') + shift) % 26
            result.append(chr(shifted + ord('a')))
        else:
            result.append(ch)   # spaces, digits, punctuation unchanged
    return ''.join(result)


def caesar_decrypt(ciphertext: str, shift: int) -> str:
    """Decrypt Caesar Cipher by reversing the shift."""
    return caesar_encrypt(ciphertext, -shift)


# ---------------------------------------------------------------------------
# Vigenere Cipher
# ---------------------------------------------------------------------------

def _vigenere_char(ch: str, key_ch: str, encrypt: bool) -> str:
    """
    Shift a single alphabetic character using the Vigenere key character.
    Non-alphabetic characters are returned unchanged (key index does NOT advance).
    """
    if not ch.isalpha():
        return ch

    base = ord('A') if ch.isupper() else ord('a')
    key_shift = ord(key_ch.upper()) - ord('A')   # key is always treated as uppercase

    if encrypt:
        shifted = (ord(ch) - base + key_shift) % 26
    else:
        shifted = (ord(ch) - base - key_shift) % 26

    return chr(base + shifted)


def vigenere_encrypt(plaintext: str, keyword: str) -> str:
    """
    Encrypt *plaintext* using Vigenere Cipher with *keyword*.

    The keyword cycles only over alphabetic characters in the plaintext;
    non-alphabetic characters pass through unchanged.

    Parameters
    ----------
    plaintext : str
    keyword   : str  (case-insensitive)

    Returns
    -------
    str  ciphertext
    """
    if not keyword:
        raise ValueError("Vigenere keyword must not be empty.")

    keyword = keyword.upper()
    result = []
    key_idx = 0

    for ch in plaintext:
        encrypted_ch = _vigenere_char(ch, keyword[key_idx % len(keyword)], encrypt=True)
        result.append(encrypted_ch)
        if ch.isalpha():          # advance key index only for alpha chars
            key_idx += 1

    return ''.join(result)


def vigenere_decrypt(ciphertext: str, keyword: str) -> str:
    """
    Decrypt Vigenere Cipher.

    Parameters
    ----------
    ciphertext : str
    keyword    : str  (case-insensitive)

    Returns
    -------
    str  plaintext
    """
    if not keyword:
        raise ValueError("Vigenere keyword must not be empty.")

    keyword = keyword.upper()
    result = []
    key_idx = 0

    for ch in ciphertext:
        decrypted_ch = _vigenere_char(ch, keyword[key_idx % len(keyword)], encrypt=False)
        result.append(decrypted_ch)
        if ch.isalpha():
            key_idx += 1

    return ''.join(result)


# ---------------------------------------------------------------------------
# Combined dual-encryption convenience functions
# ---------------------------------------------------------------------------

def dual_encrypt(message: str, caesar_shift: int, vigenere_key: str) -> str:
    """
    Apply Caesar Cipher then Vigenere Cipher to *message*.

    Step 1: Caesar  → intermediate ciphertext
    Step 2: Vigenere on intermediate → final ciphertext
    """
    after_caesar   = caesar_encrypt(message, caesar_shift)
    after_vigenere = vigenere_encrypt(after_caesar, vigenere_key)
    return after_vigenere


def dual_decrypt(ciphertext: str, caesar_shift: int, vigenere_key: str) -> str:
    """
    Reverse dual encryption: Vigenere decrypt then Caesar decrypt.

    Step 1: Vigenere decrypt → intermediate
    Step 2: Caesar  decrypt  → original plaintext
    """
    after_vigenere = vigenere_decrypt(ciphertext, vigenere_key)
    after_caesar   = caesar_decrypt(after_vigenere, caesar_shift)
    return after_caesar
