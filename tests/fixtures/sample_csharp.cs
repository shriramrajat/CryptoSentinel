using System;
using System.Security.Cryptography;
using System.Text;

namespace CryptoDemo
{
    class Program
    {
        static void Main(string[] args)
        {
            // MD5 and SHA1
            using (MD5 md5 = MD5.Create())
            {
                byte[] hash = md5.ComputeHash(Encoding.UTF8.GetBytes("test"));
            }

            using (SHA1 sha1 = SHA1.Create())
            {
                byte[] hash = sha1.ComputeHash(Encoding.UTF8.GetBytes("test"));
            }

            // AES and RSA
            using (Aes aes = Aes.Create())
            {
                aes.KeySize = 256;
            }

            using (RSACryptoServiceProvider rsa = new RSACryptoServiceProvider(2048))
            {
                // RSA provider created
            }
        }
    }
}
