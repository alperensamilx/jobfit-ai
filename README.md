# JobFit AI

CV'ni (PDF) ve bir iş ilanının metnini yükle — Claude, ikisini karşılaştırıp yapılandırılmış bir uyum raporu (0-100 skor, güçlü yönler, eksik beceriler, kısa özet) üretsin.

## Nasıl çalışır

1. CV'ni PDF olarak yükle, iş ilanının tam metnini yapıştır.
2. `pypdf` ile PDF'ten metin bellekte çıkarılır (dosyanın kendisi hiç diske/veritabanına yazılmaz).
3. Çıkarılan metin + ilan metni, Claude'a **tool use (function calling)** ile gönderilir — model serbest metin yerine tanımlı bir şemaya (`match_score`, `strengths`, `missing_skills`, `summary`) uyan yapılandırılmış bir yanıt üretmeye zorlanır. Bu, "JSON döndür" diye prompt'ta rica edip regex ile parse etmeye kıyasla çok daha güvenilir bir yöntemdir.
4. Sonuç veritabanına kaydedilir, geçmişten tekrar görüntülenebilir.

## Ekran Görüntüleri

> `screenshots/` klasörüne eklenecek.

## Teknoloji

- **Backend**: Django 4.2
- **PDF işleme**: pypdf (bellekte, dosya diske yazılmadan)
- **AI**: Anthropic Claude API (`claude-sonnet-5`), structured output için tool use pattern'i
- **Arayüz**: Bootstrap 5 (CDN)
- **Veritabanı**: SQLite

## Kurulum

```bash
git clone <bu-repo>
cd jobfit-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env dosyasını aç, ANTHROPIC_API_KEY'i kendi anahtarınla değiştir
python manage.py migrate
python manage.py runserver
```

`http://127.0.0.1:8000` adresine git, bir CV PDF'i ve bir iş ilanı metni ile dene.

## Testler

```bash
python manage.py test matcher
```

9 test: PDF metin çıkarma (geçerli ve bozuk dosyalarla), form doğrulama, tam analiz akışı, skor sınırlama (0-100), sonuç/geçmiş sayfaları. Claude API'ye **hiçbir test sırasında gerçekten gidilmez** — `analyze_fit` fonksiyonu mock'lanır, böylece testler ücretsiz, hızlı ve deterministik çalışır.

## Neden Celery/async yok?

OrderLens'ten (başka bir projem) farklı olarak burada tek bir Claude API çağrısı yapılıyor — birkaç saniye süren, pandas/matplotlib gibi ağır olmayan bir işlem. Bu yüzden bilinçli olarak senkron request/response yeterli görüldü; gereksiz karmaşıklık eklenmedi.

## Proje Yapısı

```
matcher/
  models.py        # Analysis modeli (cv_text, job_description, match_score, strengths, missing_skills, summary)
  pdf_utils.py      # PDF'ten metin çıkarma (bellekte, hata yönetimli)
  claude_client.py  # Claude API entegrasyonu — tool use ile yapılandırılmış çıktı
  views.py          # analyze / result / history view'ları
  forms.py          # yükleme formu (PDF uzantı/boyut doğrulaması)
  tests.py          # mock'lanmış Claude API ile test paketi
  templates/        # Bootstrap tabanlı şablonlar
```

## Lisans

MIT
