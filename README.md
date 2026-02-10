# 🐳 PWD Automator

Play with Docker'a otomatik giriş yapıp instance oluşturan ve komut çalıştıran bot.

**Bilgisayar gerektirmez** — GitHub Actions üzerinde çalışır,
telefondan tek tuşla tetiklenir.

---

## 🚀 Kurulum (Telefondan 5 Dakikada)

### Adım 1: GitHub Hesabı
GitHub hesabınız yoksa [github.com](https://github.com) adresinden açın.

### Adım 2: Repo Oluşturun
1. GitHub'da sağ üstteki **+** → **New repository**
2. İsim: `pwd-automator`
3. **Private** seçin (şifreleriniz gizli kalsın!)
4. **Create repository**

### Adım 3: Dosyaları Yükleyin
Yukarıdaki tüm dosyaları repo'nuza yükleyin:
1. **Add file** → **Create new file**
2. Her dosyayı tek tek oluşturun
3. Klasör oluşturmak için dosya adına `klasor/dosya.py` yazın
   - Örnek: `.github/workflows/run.yml`

### Adım 4: Secrets Ayarlayın (ÖNEMLİ!)
1. Repo → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** tıklayın
3. İsim: `ACCOUNTS_JSON`
4. Değer olarak aşağıdaki JSON'u yazın (kendi bilgilerinizle):

```json
{
  "command_file": "command.txt",
  "accounts": [
    {
      "email": "hesap1@mail.com",
      "password": "sifre1",
      "enabled": true
    },
    {
      "email": "hesap2@mail.com",
      "password": "sifre2",
      "enabled": true
    },
    {
      "email": "hesap3@mail.com",
      "password": "sifre3",
      "enabled": true
    },
    {
      "email": "hesap4@mail.com",
      "password": "sifre4",
      "enabled": true
    },
    {
      "email": "hesap5@mail.com",
      "password": "sifre5",
      "enabled": true
    }
  ]
}
