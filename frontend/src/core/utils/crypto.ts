import CryptoJS from 'crypto-js';

const TRANSMISSION_KEY = CryptoJS.enc.Utf8.parse('Tiga_Transmission_Key_32bytes!!!');
const TRANSMISSION_IV = CryptoJS.enc.Utf8.parse('Tiga_Init_16byte');

/**
 * Encrypts sensitive fields for API transmission to avoid plain text over the network.
 * @param text The plain text to encrypt
 * @returns Base64 encoded ciphertext
 */
export const encryptForTransmission = (text: string): string => {
  if (!text) return text;
  const encrypted = CryptoJS.AES.encrypt(text, TRANSMISSION_KEY, {
    iv: TRANSMISSION_IV,
    mode: CryptoJS.mode.CBC,
    padding: CryptoJS.pad.Pkcs7,
  });
  // Prepend a custom prefix to identify it as transmission-encrypted
  return `enc_trans::${encrypted.toString()}`;
};

/**
 * Decrypts transmission-encrypted fields if needed on the frontend.
 */
export const decryptFromTransmission = (ciphertext: string): string => {
  if (!ciphertext || !ciphertext.startsWith('enc_trans::')) return ciphertext;
  const actualCiphertext = ciphertext.replace('enc_trans::', '');
  const decrypted = CryptoJS.AES.decrypt(actualCiphertext, TRANSMISSION_KEY, {
    iv: TRANSMISSION_IV,
    mode: CryptoJS.mode.CBC,
    padding: CryptoJS.pad.Pkcs7,
  });
  return decrypted.toString(CryptoJS.enc.Utf8);
};
