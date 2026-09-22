// Rust Cryptographic Detection Fixture
use aes_gcm::{Aes256Gcm, Key, Nonce};
use rsa::{RsaPrivateKey, RsaPublicKey};
use sha2::Sha256;

fn rust_crypto_demo() {
    // Weak Hashing
    let weak_md5 = md5::compute(b"hello world");
    let weak_sha1 = sha1::Sha1::from("hello world");

    // RSA Generation
    let mut rng = rand::thread_rng();
    let bits = 2048;
    let private_key = RsaPrivateKey::new(&mut rng, bits).expect("failed to generate key");

    // AES GCM
    let key = Key::<Aes256Gcm>::from_slice(b"an example very secret key 32bytes");
}
