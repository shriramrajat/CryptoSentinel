# Terraform GCP Cloud KMS reference (demo)
resource "google_kms_key_ring" "main" {
  name     = "cryptosentinel-keyring"
  location = "us-east1"
}

resource "google_kms_crypto_key" "signing" {
  name     = "signing-key"
  key_ring = google_kms_key_ring.main.id
  purpose  = "ASYMMETRIC_SIGN"
  # projects/my-project/locations/us-east1/keyRings/cryptosentinel-keyring
}
