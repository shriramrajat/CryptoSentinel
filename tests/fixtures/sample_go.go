// Phase 1 Go crypto detection fixture

package main

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/des"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/hmac"
	"crypto/md5"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha1"
	"crypto/sha256"
	"crypto/sha512"
	"golang.org/x/crypto/pbkdf2"
	"golang.org/x/crypto/scrypt"
)

// RSA key generation
func generateRSA() (*rsa.PrivateKey, error) {
	return rsa.GenerateKey(rand.Reader, 2048)
}

// ECDSA key generation
func generateECDSA() (*ecdsa.PrivateKey, error) {
	return ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
}

// AES-GCM encryption
func encryptAES(key, data []byte) ([]byte, error) {
	block, _ := aes.NewCipher(key)
	gcm, _ := cipher.NewGCM(block)
	return gcm.Seal(nil, make([]byte, gcm.NonceSize()), data, nil), nil
}

// DES (legacy)
func legacyDES(key, data []byte) {
	des.NewCipher(key)
}

// 3DES (legacy)
func legacy3DES(key []byte) {
	des.NewTripleDESCipher(key)
}

// SHA-256 hash
func hashSHA256(data []byte) []byte {
	h := sha256.New()
	h.Write(data)
	return h.Sum(nil)
}

// SHA-512 hash
func hashSHA512(data []byte) []byte {
	h := sha512.New()
	h.Write(data)
	return h.Sum(nil)
}

// SHA-1 (legacy)
func hashSHA1(data []byte) []byte {
	h := sha1.New()
	h.Write(data)
	return h.Sum(nil)
}

// MD5 (legacy)
func hashMD5(data []byte) []byte {
	h := md5.New()
	h.Write(data)
	return h.Sum(nil)
}

// HMAC-SHA256
func computeHMAC(key, data []byte) []byte {
	return hmac.New(sha256.New, key).Sum(data)
}

// PBKDF2
func deriveKey(password, salt []byte) []byte {
	return pbkdf2.Key(password, salt, 100000, 32, sha256.New)
}

// scrypt
func deriveScrypt(password, salt []byte) ([]byte, error) {
	return scrypt.Key(password, salt, 32768, 8, 1, 32)
}
