# SARTAROSHXONALAR BOT — Testing Guide

Ushbu qo'llanma orqali botni mahalliy kompyuteringizda ishga tushirib, barcha funksiyalarini tekshirib ko'rishingiz mumkin.

## 1. Ishga tushirish

Terminalda quyidagi buyruqni bering:

```bash
python -m app.main
```

Agar xatolik chiqsa `pip install -r requirements.txt` buyrug'ini tering.

Bot ishga tushgach, Telegramdagi botingizga kiring.

## 2. Adminni tekshirish

1. `config.py` faylida `ADMIN_IDS` ro'yxatiga o'z Telegram ID raqamingizni yozing (agar yozilmagan bo'lsa).
2. Botga `/start` bosing.
3. Agar siz admin bo'lsangiz, **"🔐 Admin panel"** menyusi chiqishi kerak.
4. **"📊 Statistika"** tugmasini bosib tekshiring (boshida 0 bo'ladi).
5. **"➕ Admin qo'shish"** orqali boshqa odamni admin qilib ko'ring.

## 3. Sartarosh (Barber) ro'yxatdan o'tishi

1. Yangi Telegram akkauntdan (yoki admin panelidan o'zingizni o'chirib) `/start` bosing.
2. **"💈 Sartarosh"** rolni tanlang.
3. Ro'yxatdan o'tish qadamlarini bajaring:
   - Ism
   - Telefon (kontakt yuborish)
   - Viloyat va Tuman
   - Salon nomi
   - Rasm (ixtiyoriy rasm yuboring)
   - Lokatsiya
4. Tasdiqlash bosqichida **"✅ Tasdiqlash"** ni bosing.
5. Sizga "Admin tasdiqlashini kuting" xabari keladi.
6. **Admin akkauntidan** kiring:
   - Sizga yangi sartarosh haqida xabar kelgan bo'lishi kerak.
   - **"✅ Tasdiqlash"** tugmasini bosing.
7. **Sartarosh akkauntiga** "Profilingiz tasdiqlandi" degan xabar boradi. `/start` bossangiz Sartarosh menyusi ochiladi.

## 4. Sartarosh menyusi va sozlamalar

Sartarosh menyusida quyidagilarni bajaring (bu qidiruvda chiqish uchun kerak):
1. **"💰 Narxlar"**: Soch, soqol va kuyov narxlarini kiriting.
2. **"📅 Ish jadvali"**: Ish vaqtlarini belgilang (kamida bitta vaqtni ✅ qiling).
3. **"📸 Qilingan ishlar"**: Bir nechta rasm yuklab ko'ring.

## 5. Klient (Client) ro'yxatdan o'tishi

1. Uchinchi akkauntdan (yoki o'zingizni o'chirib) `/start` bosing.
2. **"👤 Klient"** rolni tanlang.
3. Ism va telefonni yuboring.
4. Klient menyusi ochiladi.

## 6. Qidiruv va Bron qilish (Booking)

1. Klient menyusida **"🔍 Yaqin sartarosh topish"** ni bosing.
2. **"📍 Lokatsiya bo'yicha"** yoki **"🔎 Qo'lda qidirish"** ni tanlang.
   - Lokatsiya yuborsangiz, yaqin atrofdagi (siz boya qo'shgan) sartarosh chiqishi kerak.
3. Sartarosh kartochkasini ko'ring, narxlar va rasmlar to'g'riligini tekshiring.
4. **"📅 Bron vaqtni tanlash"** ni bosing.
5. Bo'sh vaqtni (✅) tanlang.
6. **"✅ Tasdiqlash"** ni bosing.
7. Klientga "Bron tasdiqlandi" xabari, Sartaroshga "Yangi bron" xabari boradi.

## 7. Xizmatni yakunlash va Reyting

1. Sartarosh menyusiga qayting.
2. **"📅 Ish jadvali"** yoki **"💺 Bronlar"** bo'limiga kiring.
3. Band qilingan vaqtni (💺) bosing.
4. **"✅ Bajarildi"** tugmasini bosing.
5. Klientga "Xizmat bajarildi, baholang" xabari boradi.
6. Klient 5 yulduz qo'yib, izoh yozsin.
7. Sartarosh menyusida **"⭐ Reytingim"** ga kirib, yangi reytingni ko'ring.

## 8. Boshqa funksiyalar

- **Tilni o'zgartirish**: Sozlamalar bo'limidan tilni Ru/Uz qilib ko'ring.
- **Broadcast**: Admin panelidan hammaga xabar yuborib ko'ring.
- **Bloklash**: Admin sartaroshni bloklasa, sartarosh menyusi ishlamay qolishi kerak.

Ushbu testlardan muvaffaqiyatli o'tsa, bot to'liq ishlashga tayyor!
