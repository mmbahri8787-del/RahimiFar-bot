from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ForumTopic, Message
from aiogram import Router
import asyncio
import logging

# توکن باتت رو اینجا بذار (حتی همون توکن قبلی که دادی هم کار می‌کنه)
TOKEN = "8354876212:AAGT6FQ_tQsSpiKqY7pQojovnT8L3H-bCbs"  # ← عوضش کن با توکن جدیدت اگه گرفتی

# آیدی عددی ادمین‌ها (عدد، نه یوزرنیم) — هر چند نفر که می‌خوای اضافه کن
ADMINS = [
    5320837657, 
    5542964699,  
        # همینجا عددهای جدید اضافه کن
]

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher()
router = Router()

# دیکشنری برای نگهداری تاپیک هر کاربر
user_topics = {}  # {user_id: message_thread_id}

async def get_or_create_topic(user_id: int, full_name: str, username: str = None) -> int:
    if user_id in user_topics:
        return user_topics[user_id]

    topic_name = f"{full_name}"
    if username:
        topic_name += f" (@{username})"

    # ساخت تاپیک جدید داخل چت بات
    topic: ForumTopic = await bot.create_forum_topic(
        chat_id=bot.id,  # مهم! چت بات خودش
        name=topic_name,
        icon_custom_emoji_id="5373142718059059279"  # ایموجی کاربر دلخواه
    )

    thread_id = topic.message_thread_id
    user_topics[user_id] = thread_id

    # اطلاع به ادمین‌ها که کاربر جدید اومده
    welcome_text = f"""
کاربر جدید وارد شد
نام: {full_name}
یوزرنیم: @{username}  
آیدی: <code>{user_id}</code>
تاپیک: #{thread_id}
"""
    for admin in ADMINS:
        try:
            await bot.send_message(admin, welcome_text)
        except:
            pass

    return thread_id

# وقتی کاربر استارت می‌زنه
@router.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "سلام به سیستم پشتیبانی رحیمی‌فر نیوز \n"
        "هر پیامی بفرستید، تیم پشتیبانی در اسرع وقت جواب می‌ده "
    )

# پیام‌های کاربر → میره داخل تاپیک اختصاصی
@router.message(F.chat.type == "private", ~F.from_user.id.in_(ADMINS))
async def user_message(message: types.Message):
    user = message.from_user
    thread_id = await get_or_create_topic(
        user.id,
        user.full_name,
        user.username
    )

    # فوروارد پیام کاربر به تاپیک خودش
    await message.forward(
        chat_id=bot.id,
        message_thread_id=thread_id
    )

    await message.answer("پیام شما دریافت شد، در حال بررسی هستیم...")

# وقتی ادمین توی تاپیک جواب می‌ده → به کاربر می‌رسه
@router.message(F.message_thread_id, F.from_user.id.in_(ADMINS))
async def admin_reply(message: types.Message):
    if not message.reply_to_message:
        return

    # پیدا کردن کاربر از روی پیام فوروارد شده
    if message.reply_to_message.forward_from:
        target_user_id = message.reply_to_message.forward_from.id
        
        # کپی پیام ادمین به چت خصوصی کاربر
        await bot.copy_message(
            chat_id=target_user_id,
            from_chat_id=bot.id,
            message_id=message.message_id
        )
        
        # اختیاری: تأیید برای ادمین
        await message.answer("ارسال شد به کاربر")

# دستور اضافه کردن ادمین جدید (فقط صاحب اصلی بات)
@router.message(Command("addadmin"), F.from_user.id == ADMINS[0])  # فقط ادمین اول
async def add_admin(message: types.Message):
    if not message.reply_to_message:
        return await message.answer("لطفاً روی پیام کاربر ریپلای کنید")

    new_admin_id = message.reply_to_message.from_user.id
    if new_admin_id in ADMINS:
        return await message.answer("این فرد قبلاً ادمین است")

    ADMINS.append(new_admin_id)
    await message.answer(f"ادمین جدید اضافه شد:\n{new_admin_id}")

# دستور لیست ادمین‌ها
@router.message(Command("admins"), F.from_user.id.in_(ADMINS))
async def list_admins(message: types.Message):
    text = "لیست ادمین‌ها:\n"
    for admin in ADMINS:
        text += f"• <code>{admin}</code>\n"
    await message.answer(text)

dp.include_router(router)
if name == "main":
    asyncio.run(main())

async def main():
    logging.basicConfig(level=logging.INFO)
    print("بات پشتیبانی رحیمی‌فر نیوز با تاپیک فعال شد!")
    await dp.start_polling(bot)
