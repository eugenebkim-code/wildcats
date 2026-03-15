"""All translatable strings and species/type lists."""

SPECIES: dict[str, dict[str, str]] = {
    "steppe_cat":      {"ru": "Степной кот",       "uz": "Dasht mushugi",     "en": "Steppe Cat"},
    "jungle_cat":      {"ru": "Камышовый кот",      "uz": "Qamish mushugi",    "en": "Jungle Cat"},
    "sand_cat":        {"ru": "Барханный кот",       "uz": "Qum mushugi",       "en": "Sand Cat"},
    "caracal":         {"ru": "Каракал",             "uz": "Qorakuloq",         "en": "Caracal"},
    "turkestan_lynx":  {"ru": "Туркестанская рысь",  "uz": "Turkiston vashshasi","en": "Turkestan Lynx"},
    "snow_leopard":    {"ru": "Снежный барс",        "uz": "Qor qoploni",       "en": "Snow Leopard"},
    "unsure":          {"ru": "Не уверен",           "uz": "Aniq emas",         "en": "Not sure"},
}

OBS_TYPES: dict[str, dict[str, str]] = {
    "photo_animal": {"ru": "📷 Фото животного",              "uz": "📷 Hayvon fotosurati",       "en": "📷 Photo of animal"},
    "photo_tracks": {"ru": "🐾 Фото следов / помёта",        "uz": "🐾 Iz / chiqindi fotosi",    "en": "🐾 Photo of tracks / scat"},
    "visual":       {"ru": "👁 Визуальная встреча (без фото)","uz": "👁 Ko'rish orqali (fotosiz)","en": "👁 Visual sighting (no photo)"},
}

TEXTS: dict[str, dict[str, str]] = {
    "ru": {
        # ── language & welcome ──────────────────────────────────────────
        "select_language": "🌍 Выберите язык / Choose language / Tilni tanlang:",
        "welcome": (
            "🐆 *Дикие кошки Узбекистана*\n\n"
            "Добро пожаловать! Этот бот помогает собирать данные о встречах редких диких кошек "
            "на территории Узбекистана для научного мониторинга.\n\n"
            "Ваши наблюдения помогают защитить редкие виды! 🌿"
        ),
        "add_observation": "➕ Добавить наблюдение",
        # ── step 1 ──────────────────────────────────────────────────────
        "step_species": "🐱 *Шаг 1 из 8 — Вид животного*\n\nВыберите вид кошки, которую вы наблюдали:",
        # ── step 2 ──────────────────────────────────────────────────────
        "step_obs_type": "📋 *Шаг 2 из 8 — Тип наблюдения*\n\nВыберите тип вашего наблюдения:",
        # ── step 3 ──────────────────────────────────────────────────────
        "step_photos": (
            "📸 *Шаг 3 из 8 — Фотографии*\n\n"
            "Как загрузить фото:\n"
            "📎 Нажмите на *скрепку* (вложение) внизу экрана → выберите фото из галереи\n\n"
            "Отправьте одно или несколько фото.\n"
            "Когда закончите — нажмите «Готово».\n\n"
            "Если фото нет — нажмите «Пропустить»."
        ),
        "photo_added": "✅ Фото добавлено ({count}). Отправьте ещё или нажмите «Готово».",
        "photos_done": "Готово ✓",
        "skip": "Пропустить →",
        # ── step 4 ──────────────────────────────────────────────────────
        "step_date": (
            "📅 *Шаг 4 из 8 — Дата встречи*\n\n"
            "Введите дату, когда произошла встреча.\n"
            "Формат: ДД.ММ.ГГГГ\n"
            "Пример: `14.05.2025`"
        ),
        "date_invalid": (
            "❌ Неверный формат даты.\n"
            "Пожалуйста, используйте формат *ДД.ММ.ГГГГ*\n"
            "Пример: `14.05.2025`"
        ),
        "date_future": "❌ Дата не может быть в будущем. Укажите корректную дату встречи.",
        # ── step 5 ──────────────────────────────────────────────────────
        "step_location": "📍 *Шаг 5 из 8 — Место встречи*\n\nУкажите место, где вы наблюдали животное:",
        "location_current":      "📍 Отправить текущую геолокацию",
        "location_map":          "🗺 Указать место на карте",
        "location_manual":       "⌨ Ввести координаты вручную",
        "location_current_hint": (
            "📍 Используйте эту кнопку, если вы *сейчас* находитесь в месте наблюдения.\n\n"
            "Нажмите кнопку ниже, чтобы отправить геолокацию:"
        ),
        "location_map_hint": (
            "🗺 Выберите точку на карте.\n\n"
            "Нажмите кнопку ниже → выберите «Выбрать на карте»:"
        ),
        "location_manual_hint": (
            "⌨ *Введите координаты GPS:*\n\n"
            "Формат: `широта, долгота`\n"
            "Пример: `41.345678, 67.123456`"
        ),
        "location_invalid": (
            "❌ Неверный формат координат.\n"
            "Используйте формат: `широта, долгота`\n"
            "Пример: `41.345678, 67.123456`"
        ),
        "location_out_of_range": "❌ Координаты вне допустимого диапазона. Проверьте значения и повторите.",
        "location_received":     "✅ Координаты получены: `{lat}, {lon}`",
        "awaiting_geo": "📍 Нажмите кнопку ниже, чтобы поделиться геолокацией:",
        # ── step 6 ──────────────────────────────────────────────────────
        "step_location_name": (
            "🏔 *Шаг 6 из 8 — Название местности*\n\n"
            "Укажите название места (рекомендуется).\n"
            "Примеры: урочище Джейран, плато Устюрт, Кызылкум\n\n"
            "Если не знаете — нажмите «Пропустить»."
        ),
        # ── step 7 ──────────────────────────────────────────────────────
        "step_observer": (
            "👤 *Шаг 7 из 8 — Имя наблюдателя*\n\n"
            "Укажите ваше имя или никнейм (для авторства).\n"
            "Примеры: Иван Петров, @username, Алишер\n\n"
            "Для анонимной отправки нажмите «Анонимно»."
        ),
        "anonymous": "🕵 Анонимно",
        # ── step 8 ──────────────────────────────────────────────────────
        "step_notes": (
            "📝 *Шаг 8 из 8 — Дополнительные сведения*\n\n"
            "Добавьте любую дополнительную информацию о встрече "
            "(поведение животного, условия наблюдения, количество особей и т.д.).\n\n"
            "Если нечего добавить — нажмите «Пропустить»."
        ),
        # ── confirmation ────────────────────────────────────────────────
        "confirmation_title":           "✅ *Проверьте данные наблюдения:*",
        "confirmation_species":         "🐱 Вид: {value}",
        "confirmation_obs_type":        "📋 Тип: {value}",
        "confirmation_date":            "📅 Дата: {value}",
        "confirmation_coords":          "📍 Координаты: `{lat}, {lon}`",
        "confirmation_no_coords":       "📍 Координаты: не указаны",
        "confirmation_location_name":   "🏔 Местность: {value}",
        "confirmation_no_location_name":"🏔 Местность: не указана",
        "confirmation_observer":        "👤 Наблюдатель: {value}",
        "confirmation_photos":          "📸 Фото: {count} шт.",
        "confirmation_no_photos":       "📸 Фото: нет",
        "confirmation_notes":           "📝 Примечания: {value}",
        "confirmation_no_notes":        "📝 Примечания: нет",
        "btn_send":  "✅ Отправить",
        "btn_edit":  "✏️ Изменить",
        "success": (
            "🎉 *Наблюдение успешно сохранено!*\n\n"
            "ID наблюдения: `#{obs_id}`\n\n"
            "Спасибо за ваш вклад в защиту дикой природы Узбекистана! 🐆"
        ),
        # ── edit menu ───────────────────────────────────────────────────
        "edit_choose_field":    "✏️ *Что вы хотите изменить?*",
        "edit_species":         "🐱 Вид",
        "edit_obs_type":        "📋 Тип наблюдения",
        "edit_photos":          "📸 Фото",
        "edit_date":            "📅 Дата",
        "edit_location":        "📍 Координаты",
        "edit_location_name":   "🏔 Местность",
        "edit_observer":        "👤 Наблюдатель",
        "edit_notes":           "📝 Примечания",
        "back_to_confirmation": "← Назад к подтверждению",
        # ── misc ────────────────────────────────────────────────────────
        "cancelled": "❌ Отменено. Нажмите «Добавить наблюдение», чтобы начать заново.",
        "error_generic": "❌ Произошла ошибка. Попробуйте ещё раз или начните заново с /start",
        "share_location_btn": "📍 Поделиться геолокацией",
    },

    "uz": {
        "select_language": "🌍 Выберите язык / Choose language / Tilni tanlang:",
        "welcome": (
            "🐆 *O'zbekiston yovvoyi mushuqlari*\n\n"
            "Xush kelibsiz! Bu bot O'zbekiston hududida noyob yovvoyi mushuqlarni kuzatish "
            "ma'lumotlarini ilmiy monitoring uchun yig'adi.\n\n"
            "Sizning kuzatishlaringiz noyob turlarni himoya qilishga yordam beradi! 🌿"
        ),
        "add_observation": "➕ Kuzatish qo'shish",
        "step_species": "🐱 *8 dan 1-qadam — Hayvon turi*\n\nKuzatgan mushugingiz turini tanlang:",
        "step_obs_type": "📋 *8 dan 2-qadam — Kuzatish turi*\n\nKuzatish turini tanlang:",
        "step_photos": (
            "📸 *8 dan 3-qadam — Fotosuratlar*\n\n"
            "Foto yuborish uchun:\n"
            "📎 Pastdagi *qisqich* (fayl) tugmasini bosing → galereyadan foto tanlang\n\n"
            "Bir yoki bir nechta foto yuboring.\n"
            "Tugatgach — «Tayyor» tugmasini bosing.\n\n"
            "Foto yo'q bo'lsa — «O'tkazib yuborish» ni bosing."
        ),
        "photo_added": "✅ Foto qo'shildi ({count}). Yana yuboring yoki «Tayyor» ni bosing.",
        "photos_done": "Tayyor ✓",
        "skip": "O'tkazib yuborish →",
        "step_date": (
            "📅 *8 dan 4-qadam — Uchrashuv sanasi*\n\n"
            "Uchrashuv sodir bo'lgan sanani kiriting.\n"
            "Format: KK.OO.YYYY\n"
            "Misol: `14.05.2025`"
        ),
        "date_invalid": (
            "❌ Sana formati noto'g'ri.\n"
            "*KK.OO.YYYY* formatidan foydalaning\n"
            "Misol: `14.05.2025`"
        ),
        "date_future": "❌ Sana kelajakda bo'lishi mumkin emas. To'g'ri sanani kiriting.",
        "step_location": "📍 *8 dan 5-qadam — Uchrashuv joyi*\n\nHayvonni kuzatgan joyingizni ko'rsating:",
        "location_current":      "📍 Joriy joylashuvni yuborish",
        "location_map":          "🗺 Xaritada joy ko'rsatish",
        "location_manual":       "⌨ Koordinatalarni qo'lda kiritish",
        "location_current_hint": (
            "📍 Agar hozir kuzatuv joyida bo'lsangiz ushbu tugmadan foydalaning.\n\n"
            "Quyidagi tugmani bosib joylashuvni yuboring:"
        ),
        "location_map_hint": (
            "🗺 Xaritada nuqtani belgilang.\n\n"
            "Quyidagi tugmani bosing → «Xaritada tanlash» ni tanlang:"
        ),
        "location_manual_hint": (
            "⌨ *GPS koordinatalarini kiriting:*\n\n"
            "Format: `kenglik, uzunlik`\n"
            "Misol: `41.345678, 67.123456`"
        ),
        "location_invalid": (
            "❌ Koordinatalar formati noto'g'ri.\n"
            "Format: `kenglik, uzunlik`\n"
            "Misol: `41.345678, 67.123456`"
        ),
        "location_out_of_range": "❌ Koordinatalar diapazondan tashqarida. Qiymatlarni tekshiring.",
        "location_received":     "✅ Koordinatalar qabul qilindi: `{lat}, {lon}`",
        "awaiting_geo": "📍 Joylashuvni ulashish uchun quyidagi tugmani bosing:",
        "step_location_name": (
            "🏔 *8 dan 6-qadam — Joylashuv nomi*\n\n"
            "Joy nomini kiriting (tavsiya etiladi).\n"
            "Misollar: Jayron urochishchasi, Ustyurt platosi, Qizilqum\n\n"
            "Bilmasangiz — «O'tkazib yuborish» ni bosing."
        ),
        "step_observer": (
            "👤 *8 dan 7-qadam — Kuzatuvchi ismi*\n\n"
            "Ismingiz yoki taxallusIngizni kiriting (muallif uchun).\n"
            "Misollar: Alisher Nazarov, @username\n\n"
            "Anonim yuborish uchun «Anonim» ni bosing."
        ),
        "anonymous": "🕵 Anonim",
        "step_notes": (
            "📝 *8 dan 8-qadam — Qo'shimcha ma'lumotlar*\n\n"
            "Uchrashuv haqida qo'shimcha ma'lumot qo'shing "
            "(hayvon xulqi, kuzatish sharoitlari, nusxalar soni va h.k.).\n\n"
            "Qo'shish kerak bo'lmasa — «O'tkazib yuborish» ni bosing."
        ),
        "confirmation_title":           "✅ *Kuzatish ma'lumotlarini tekshiring:*",
        "confirmation_species":         "🐱 Tur: {value}",
        "confirmation_obs_type":        "📋 Tur: {value}",
        "confirmation_date":            "📅 Sana: {value}",
        "confirmation_coords":          "📍 Koordinatalar: `{lat}, {lon}`",
        "confirmation_no_coords":       "📍 Koordinatalar: ko'rsatilmagan",
        "confirmation_location_name":   "🏔 Joy: {value}",
        "confirmation_no_location_name":"🏔 Joy: ko'rsatilmagan",
        "confirmation_observer":        "👤 Kuzatuvchi: {value}",
        "confirmation_photos":          "📸 Fotolar: {count} ta",
        "confirmation_no_photos":       "📸 Fotolar: yo'q",
        "confirmation_notes":           "📝 Izohlar: {value}",
        "confirmation_no_notes":        "📝 Izohlar: yo'q",
        "btn_send": "✅ Yuborish",
        "btn_edit": "✏️ O'zgartirish",
        "success": (
            "🎉 *Kuzatish muvaffaqiyatli saqlandi!*\n\n"
            "Kuzatish ID: `#{obs_id}`\n\n"
            "O'zbekiston yovvoyi tabiatini himoya qilishga hissangiz uchun rahmat! 🐆"
        ),
        "edit_choose_field":    "✏️ *Nimani o'zgartirmoqchisiz?*",
        "edit_species":         "🐱 Tur",
        "edit_obs_type":        "📋 Kuzatish turi",
        "edit_photos":          "📸 Fotolar",
        "edit_date":            "📅 Sana",
        "edit_location":        "📍 Koordinatalar",
        "edit_location_name":   "🏔 Joy nomi",
        "edit_observer":        "👤 Kuzatuvchi",
        "edit_notes":           "📝 Izohlar",
        "back_to_confirmation": "← Tasdiqlashga qaytish",
        "cancelled": "❌ Bekor qilindi. Boshlash uchun «Kuzatish qo'shish» ni bosing.",
        "error_generic": "❌ Xatolik yuz berdi. Qayta urinib ko'ring yoki /start bilan boshlang",
        "share_location_btn": "📍 Joylashuvni ulashish",
    },

    "en": {
        "select_language": "🌍 Выберите язык / Choose language / Tilni tanlang:",
        "welcome": (
            "🐆 *Wild Cats of Uzbekistan*\n\n"
            "Welcome! This bot collects data about sightings of rare wild cats "
            "in Uzbekistan for scientific monitoring.\n\n"
            "Your observations help protect endangered species! 🌿"
        ),
        "add_observation": "➕ Add observation",
        "step_species": "🐱 *Step 1 of 8 — Animal species*\n\nSelect the cat species you observed:",
        "step_obs_type": "📋 *Step 2 of 8 — Observation type*\n\nSelect the type of your observation:",
        "step_photos": (
            "📸 *Step 3 of 8 — Photos*\n\n"
            "How to send a photo:\n"
            "📎 Tap the *paperclip* (attachment) at the bottom → choose a photo from your gallery\n\n"
            "Send one or more photos.\n"
            "When done — press «Done».\n\n"
            "If no photos — press «Skip»."
        ),
        "photo_added": "✅ Photo added ({count}). Send more or press «Done».",
        "photos_done": "Done ✓",
        "skip": "Skip →",
        "step_date": (
            "📅 *Step 4 of 8 — Date of sighting*\n\n"
            "Enter the date when the sighting occurred.\n"
            "Format: DD.MM.YYYY\n"
            "Example: `14.05.2025`"
        ),
        "date_invalid": (
            "❌ Invalid date format.\n"
            "Please use *DD.MM.YYYY*\n"
            "Example: `14.05.2025`"
        ),
        "date_future": "❌ Date cannot be in the future. Please enter a valid sighting date.",
        "step_location": "📍 *Step 5 of 8 — Location*\n\nIndicate where you observed the animal:",
        "location_current":      "📍 Share current location",
        "location_map":          "🗺 Pick location on map",
        "location_manual":       "⌨ Enter coordinates manually",
        "location_current_hint": (
            "📍 Use this if you are *currently* at the sighting location.\n\n"
            "Press the button below to share your location:"
        ),
        "location_map_hint": (
            "🗺 Pick a point on the map.\n\n"
            "Press the button below → choose «Choose on map»:"
        ),
        "location_manual_hint": (
            "⌨ *Enter GPS coordinates:*\n\n"
            "Format: `latitude, longitude`\n"
            "Example: `41.345678, 67.123456`"
        ),
        "location_invalid": (
            "❌ Invalid coordinate format.\n"
            "Use: `latitude, longitude`\n"
            "Example: `41.345678, 67.123456`"
        ),
        "location_out_of_range": "❌ Coordinates out of valid range. Please check the values.",
        "location_received":     "✅ Coordinates received: `{lat}, {lon}`",
        "awaiting_geo": "📍 Press the button below to share your location:",
        "step_location_name": (
            "🏔 *Step 6 of 8 — Location name*\n\n"
            "Enter the location name (recommended).\n"
            "Examples: Jeiran gorge, Ustyurt plateau, Kyzylkum\n\n"
            "If unknown — press «Skip»."
        ),
        "step_observer": (
            "👤 *Step 7 of 8 — Observer name*\n\n"
            "Enter your name or nickname (for authorship).\n"
            "Examples: John Smith, @username\n\n"
            "For anonymous submission press «Anonymous»."
        ),
        "anonymous": "🕵 Anonymous",
        "step_notes": (
            "📝 *Step 8 of 8 — Additional notes*\n\n"
            "Add any additional information about the sighting "
            "(animal behaviour, observation conditions, number of individuals, etc.).\n\n"
            "If nothing to add — press «Skip»."
        ),
        "confirmation_title":           "✅ *Review your observation:*",
        "confirmation_species":         "🐱 Species: {value}",
        "confirmation_obs_type":        "📋 Type: {value}",
        "confirmation_date":            "📅 Date: {value}",
        "confirmation_coords":          "📍 Coordinates: `{lat}, {lon}`",
        "confirmation_no_coords":       "📍 Coordinates: not provided",
        "confirmation_location_name":   "🏔 Location: {value}",
        "confirmation_no_location_name":"🏔 Location: not provided",
        "confirmation_observer":        "👤 Observer: {value}",
        "confirmation_photos":          "📸 Photos: {count}",
        "confirmation_no_photos":       "📸 Photos: none",
        "confirmation_notes":           "📝 Notes: {value}",
        "confirmation_no_notes":        "📝 Notes: none",
        "btn_send": "✅ Submit",
        "btn_edit": "✏️ Edit",
        "success": (
            "🎉 *Observation saved successfully!*\n\n"
            "Observation ID: `#{obs_id}`\n\n"
            "Thank you for contributing to wildlife conservation in Uzbekistan! 🐆"
        ),
        "edit_choose_field":    "✏️ *What would you like to change?*",
        "edit_species":         "🐱 Species",
        "edit_obs_type":        "📋 Observation type",
        "edit_photos":          "📸 Photos",
        "edit_date":            "📅 Date",
        "edit_location":        "📍 Coordinates",
        "edit_location_name":   "🏔 Location name",
        "edit_observer":        "👤 Observer",
        "edit_notes":           "📝 Notes",
        "back_to_confirmation": "← Back to confirmation",
        "cancelled": "❌ Cancelled. Press «Add observation» to start over.",
        "error_generic": "❌ An error occurred. Please try again or restart with /start",
        "share_location_btn": "📍 Share location",
    },
}


def t(lang: str, key: str, **kwargs: object) -> str:
    """Return translated string for lang/key, falling back to Russian."""
    text = TEXTS.get(lang, TEXTS["ru"]).get(key) or TEXTS["ru"].get(key, key)
    return text.format(**kwargs) if kwargs else text


def species_name(key: str, lang: str) -> str:
    return SPECIES.get(key, {}).get(lang, key)


def obs_type_name(key: str, lang: str) -> str:
    return OBS_TYPES.get(key, {}).get(lang, key)
