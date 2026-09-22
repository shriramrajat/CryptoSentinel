// Phase 1 TypeScript crypto detection fixture
// TypeScript should reuse JavaScript rules

import * as crypto from 'crypto';
import * as jwt from 'jsonwebtoken';

// Node.js createHash SHA-256
function hashData(data: string): string {
    return crypto.createHash('sha256').update(data).digest('hex');
}

// Node.js createCipheriv AES-256-CBC
function encryptData(key: Buffer, iv: Buffer, data: string): string {
    const cipher = crypto.createCipheriv('aes-256-cbc', key, iv);
    return cipher.update(data, 'utf8', 'hex');
}

// Node.js generateKeyPair EC
async function generateEcKey(): Promise<crypto.KeyPairKeyObjectResult> {
    return crypto.generateKeyPairSync('ec', { namedCurve: 'P-256' });
}
