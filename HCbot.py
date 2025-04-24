from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# Состояния разговора
MENU, MODEL, PHOTO, CONTACT = range(4)

# Вспомогательная: показывает inline-меню
async def send_menu(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Выбрать модель телефона", callback_data="choose_model")],
        [InlineKeyboardButton("Добавить изображение", callback_data="add_photo")],
        [InlineKeyboardButton("Поделиться контактом", callback_data="share_contact")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    # если вызвано из callback_query
    if hasattr(update_or_query, "callback_query") and update_or_query.callback_query:
        await update_or_query.callback_query.edit_message_text(
            "Главное меню; выберите действие;",
            reply_markup=markup
        )
    else:
        await update_or_query.message.reply_text(
            "Главное меню; выберите действие;",
            reply_markup=markup
        )
    return MENU

# Старт: сразу меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await send_menu(update, context)

# Обработка inline-меню
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "choose_model":
        await query.edit_message_text("Напишите, пожалуйста, модель вашего телефона;")
        return MODEL
    if query.data == "add_photo":
        await query.edit_message_text("Прикрепите изображение через кнопку «📎»;")
        return PHOTO
    if query.data == "share_contact":
        # Кнопка запроса контакта
        kb = [[KeyboardButton("📲 Поделиться контактом", request_contact=True)]]
        rm = ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
        # Обновляем сообщение меню
        await query.edit_message_text("👉 Нажмите кнопку ниже справа, чтобы передать контакт 📲")
        # Выводим кнопки под полем ввода
        await query.message.reply_text("👇", reply_markup=rm)
        return CONTACT

# Шаг MODEL → потом возвращаемся в меню
async def model_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['model'] = update.message.text
    await update.message.reply_text(f"Модель {update.message.text} сохранена;")
    return await send_menu(update, context)

# Шаг PHOTO → и снова меню
async def photo_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import os
    os.makedirs('photos', exist_ok=True)
    photo = update.message.photo[-1]
    file = await photo.get_file()
    path = f"photos/{update.effective_user.id}_{photo.file_unique_id}.jpg"
    await file.download_to_drive(path)
    context.user_data['photo_path'] = path

    await update.message.reply_text("Фото сохранено;")
    return await send_menu(update, context)

# Шаг CONTACT → завершаем
async def contact_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact.phone_number
    context.user_data['contact'] = contact
    await update.message.reply_text(
        "Контакт получен; заявка оформлена; спасибо за обращение!"
    )
    return ConversationHandler.END

# Отмена диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог отменён;")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token("7996649984:AAHW_Wxy6PSwJEPlX6RwZBt6JkL3LjtWRQA").build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU:    [CallbackQueryHandler(menu_handler)],
            MODEL:   [MessageHandler(filters.TEXT & ~filters.COMMAND, model_received)],
            PHOTO:   [MessageHandler(filters.PHOTO, photo_received)],
            CONTACT: [MessageHandler(filters.CONTACT, contact_received)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    print("Бот запущен…")
    app.run_polling()
