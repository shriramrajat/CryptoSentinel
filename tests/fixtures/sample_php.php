<?php
// PHP Cryptographic Detection Fixture

// Hash functions
$md5_hash = md5("secret_password");
$sha1_hash = sha1("secret_password");
$sha256_hash = hash("sha256", "secret_password");

// OpenSSL encryption
$cipher = "aes-256-cbc";
$key = openssl_random_pseudo_bytes(32);
$ivlen = openssl_cipher_iv_length($cipher);
$iv = openssl_random_pseudo_bytes($ivlen);
$ciphertext = openssl_encrypt("sensitive data", $cipher, $key, $options=0, $iv);

// OpenSSL RSA
$res = openssl_pkey_new(array(
    "private_key_bits" => 2048,
    "private_key_type" => OPENSSL_KEYTYPE_RSA,
));
