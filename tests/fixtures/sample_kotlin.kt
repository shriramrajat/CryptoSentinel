import java.security.MessageDigest
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import java.security.KeyPairGenerator

fun kotlinCryptoDemo() {
    val md5 = MessageDigest.getInstance("MD5")
    val sha1 = MessageDigest.getInstance("SHA-1")
    val sha256 = MessageDigest.getInstance("SHA-256")

    val keyGen = KeyGenerator.getInstance("AES")
    keyGen.init(256)
    val secretKey = keyGen.generateKey()

    val kpg = KeyPairGenerator.getInstance("RSA")
    kpg.initialize(2048)
    val keyPair = kpg.generateKeyPair()
}
