// Phase 1 JavaScript crypto detection fixture
// Tests: WebCrypto API, Node.js crypto module, JWT, node-forge

const crypto = require('crypto');
const jwt = require('jsonwebtoken');

// Node.js crypto: createHash
function hashData(data) {
    return crypto.createHash('sha256').update(data).digest('hex');
}

// Node.js crypto: MD5 (legacy)
function legacyHash(data) {
    return crypto.createHash('md5').update(data).digest('hex');
}

// Node.js crypto: createCipheriv AES-256-GCM
function encryptAES(key, iv, data) {
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    return cipher.update(data, 'utf8', 'hex');
}

// Node.js crypto: createHmac
function computeHmac(key, data) {
    return crypto.createHmac('sha256', key).update(data).digest('hex');
}

// Node.js crypto: generateKeyPair RSA
function generateRsaKey() {
    return crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
}

// JWT: sign
function signToken(payload, secret) {
    return jwt.sign(payload, secret);
}

// WebCrypto API: generateKey AES
async function generateAESKey() {
    return await window.crypto.subtle.generateKey(
        { "name": "AES-GCM", length: 256 },
        true,
        ["encrypt", "decrypt"]
    );
}

// WebCrypto API: digest SHA-256
async function hashWebCrypto(data) {
    return await window.crypto.subtle.digest("SHA-256", data);
}

// WebCrypto API: sign ECDSA
async function signECDSA(key, data) {
    return await window.crypto.subtle.sign({"name": "ECDSA", hash: "SHA-256"}, key, data);
}

// Negative test: comments and string docs should not trigger
// crypto.createCipheriv is documented here but not called
// "aes-256-cbc" in a template literal without a real call
const note = "We use aes-256-gcm for encryption";
