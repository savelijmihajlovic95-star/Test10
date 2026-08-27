# spam_plugin.py
from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
import time

# Словарь для хранения статуса спама (чтобы можно было остановить)
spam_tasks = {}

@Client.on_message(filters.command("spam", prefixes=".") & filters.me)
async def spam_command(client: Client, message: Message):
    # Проверяем аргументы
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.edit_text("❌ Использование: `.spam [количество] [текст]`")
        return
    
    try:
        count = int(args[1])
        text = args[2]
    except ValueError:
        await message.edit_text("❌ Количество должно быть числом!")
        return
    
    if count <= 0:
        await message.edit_text("❌ Количество должно быть больше 0!")
        return
    
    # Удаляем команду из чата
    await message.delete()
    
    # Получаем ID чата
    chat_id = message.chat.id
    
    # Создаём задачу для спама
    task = asyncio.create_task(spam_sender(client, chat_id, count, text))
    
    # Сохраняем задачу для возможной остановки
    spam_tasks[chat_id] = task
    
    # Отправляем уведомление о начале (только себе в ЛС)
    await client.send_message("me", f"🚀 Начинаю спам в чат {chat_id}\n📨 {count} сообщений\n⏱️ Скорость: 1 мс/сообщение")

async def spam_sender(client: Client, chat_id: int, count: int, text: str):
    """Отправляет сообщения с задержкой 1 мс"""
    try:
        for i in range(count):
            # Проверяем, не была ли задача отменена
            if asyncio.current_task().cancelled():
                break
            
            await client.send_message(chat_id, text)
            
            # Задержка 1 миллисекунда
            await asyncio.sleep(0.001)
            
            # Каждые 100 сообщений показываем прогресс (в ЛС)
            if (i + 1) % 100 == 0:
                await client.send_message("me", f"📊 Прогресс: {i + 1}/{count}")
        
        await client.send_message("me", f"✅ Спам завершён! Отправлено {count} сообщений.")
    except asyncio.CancelledError:
        await client.send_message("me", f"⛔ Спам остановлен! Отправлено {i + 1} сообщений.")
    except Exception as e:
        await client.send_message("me", f"⚠️ Ошибка: {str(e)}")
    finally:
        # Удаляем задачу из словаря
        if chat_id in spam_tasks:
            del spam_tasks[chat_id]

# Команда для остановки спама
@Client.on_message(filters.command("stopspam", prefixes=".") & filters.me)
async def stop_spam(client: Client, message: Message):
    chat_id = message.chat.id
    
    if chat_id in spam_tasks:
        spam_tasks[chat_id].cancel()
        await message.edit_text("🛑 Останавливаю спам...")
        await asyncio.sleep(0.5)
        await message.delete()
    else:
        await message.edit_text("❌ Активный спам не найден в этом чате.")
        await asyncio.sleep(1)
        await message.delete()
