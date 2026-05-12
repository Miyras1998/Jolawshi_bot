# 🚖 JolawshiBot — O'rnatish yo'riqnomasi

## 📁 Fayl tuzilmasi
```
jolawshi_bot/
├── bot.py              # Asosiy fayl
├── config.py           # Sozlamalar
├── database.py         # Ma'lumotlar bazasi
├── keyboards.py        # Tugmalar
├── requirements.txt    # Kutubxonalar
├── .env.example        # Token namunasi
└── handlers/
    ├── __init__.py
    ├── common.py       # Start, profil
    ├── passenger.py    # Yo'lovchi
    ├── driver.py       # Haydovchi
    └── admin.py        # Admin panel
```

---

## 1️⃣ BOT TOKEN OLISH

1. Telegramda **@BotFather** ga yozing
2. `/newbot` buyrug'ini yuboring
3. Bot nomini kiriting: `JolawshiBot`
4. Username kiriting: `Jolawshi_bot`
5. **Token** ni nusxalab oling (ko'rinishi: `7123456789:AAF...`)

---

## 2️⃣ ADMIN ID OLISH

1. Telegramda **@userinfobot** ga yozing
2. `/start` bosing
3. **Id** raqamini nusxalab oling (masalan: `987654321`)

---

## 3️⃣ RAILWAY.APP DA JOYLASH (BEPUL)

### a) Akkaunt ochish
1. **railway.app** ga kiring
2. **GitHub** bilan ro'yxatdan o'ting (bepul)

### b) GitHub ga yuklash
1. **github.com** ga kiring → **New repository** → `jolawshi-bot`
2. Barcha fayllarni yuklang
3. `.env.example` faylini `.env` deb nomini o'zgartiring
4. `.env` ichiga haqiqiy tokenni yozing

### c) Railway ga ulash
1. railway.app → **New Project** → **Deploy from GitHub repo**
2. `jolawshi-bot` reponi tanlang
3. **Variables** bo'limiga o'ting → quyidagilarni qo'shing:

```
BOT_TOKEN    = 7123456789:AAF...toxenингиз
ADMIN_IDS    = 987654321
CHANNEL_ID   = @Jolawshi_bot_buyirtpa
DB_PATH      = jolawshi.db
```

4. **Settings** → **Start Command**:
```
python bot.py
```

5. **Deploy** tugmasini bosing ✅

---

## 4️⃣ KANALGA BOT QO'SHISH

1. **@Jolawshi_bot_buyirtpa** kanalingizni oching
2. **Kanal sozlamalari** → **Administratorlar**
3. Botingizni qidiring va **Admin** qilib qo'shing
4. Quyidagi ruxsatlarni bering:
   - ✅ Xabarlar yuborish
   - ✅ Xabarlarni tahrirlash
   - ✅ Xabarlarni o'chirish

---

## 5️⃣ ISHGA TUSHIRISH TEKSHIRISH

Botingizga `/start` yuboring:
- ✅ Bot javob bersa — hammasi tayyor!
- ❌ Javob bermasa — token va deploy loglarini tekshiring

---

## 🛡️ ADMIN PANEL BUYRUQLARI

Botga quyidagilarni yuboring:
```
/admin — Admin panelga kirish
```

**Admin panel imkoniyatlari:**
- 📊 Statistika — foydalanuvchilar, safarlar soni
- ⚙️ Sozlamalar — vaqt, muddат, kanal
- 👥 Foydalanuvchilar — ko'rish, bloklash, xabar
- 🚗 Barcha safarlar — nazorat
- 📢 Ommaviy xabar — hammaga yuborish

---

## ⚠️ MUHIM ESLATMALAR

- `.env` faylini **hech kimga ko'rsatmang**
- Token sizning botingiz kaliti — uni sir saqlang
- Railway bepul planda oyiga **500 soat** — bu yetarli
- Bot to'xtab qolsa Railway dashboard dan restart qiling

---

## 📞 Muammo chiqsa

Telegram: @taxibot_support
