import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, LabeledPrice
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.filters.state import StatesGroup, State

import db
import config

API_TOKEN = config.BOT_TOKEN
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Admin ID (replace with your Telegram ID)
admin_id = config.ADMIN_ID

# Initialize the database
db.init_database()

db.add_category("📜 12 days shopping")
db.add_category("📜 5 days shopping")
db.add_category("📜 others")


class MyForm(StatesGroup):
    get_caption = State()
    get_description = State()
    get_price = State()
    get_media_type = State()
    get_media = State()
    get_category = State()
    get_category_name = State()


def generate_category_keyboard():
    categories = ReplyKeyboardMarkup()
    for category in db.get_all_categories():
        categories.add(category.name)
    return categories


class keyboards:
    admin_panel = ReplyKeyboardMarkup(resize_keyboard=True).add(
        "➕ Add product",
        "❌ Delete product",
        "➕ Add category",
        "❌ Delete category",
        "⤴ Back"
    )

    add_media_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
        "📷 Photo",
        "🎥 Video",
        "⤴ Back"
    )

    back_menu = ReplyKeyboardMarkup(resize_keyboard=True).add(
        "⤴ Back"
    )


# Commands
@dp.message_handler(Command('start'))
async def start(message: types.Message):
    await dp.bot.send_message(message.chat.id, "😎Hello and welcome to our store!!!\n🛒Here are all available products:",
                              reply_markup=generate_category_keyboard())


@dp.message_handler(Command('admin'))
async def admin_panel(message: types.Message):
    if message.from_user.id == admin_id:
        await dp.bot.send_message(message.chat.id, "🎉 Welcome back sir", reply_markup=keyboards.admin_panel)
    else:
        await dp.bot.send_message(message.chat.id, "You are not authorized to access the admin panel.")


@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def buttons_handler(message: types.Message, state: FSMContext):
    if message.text in [category.name for category in db.get_all_categories()]:
        products = db.get_products_by_category(message.text)
        if not products:
            await dp.bot.send_message(message.chat.id, "Seems like there's nothing in there😢")
            return
        for product in products:
            if product.media_type == "photo":
                await dp.bot.send_photo(message.chat.id, product.media_id)
            else:
                await dp.bot.send_video(message.chat.id, product.media_id)
            await dp.bot.send_invoice(message.chat.id,
                                      title=f"Buy {product.caption.capitalize()}",
                                      description=f"{product.description}",
                                      provider_token=config.PAYMENT_TOKEN,
                                      currency='USD',
                                      prices=[LabeledPrice("Product", int(product.price) * 100)],
                                      is_flexible=False,
                                      start_parameter="buy-product",
                                      payload='test-invoice-payload')
    if message.from_user.id == admin_id:
        if message.text == "❌ Delete product":
            await delete_product_command(message)
        elif message.text == "➕ Add category":
            await dp.bot.send_message(message.chat.id, "Write the name of the new category.")
            await MyForm.get_category_name.set()
        elif message.text == "❌ Delete category":
            await show_categories_for_deletion(message)


class MyForm(StatesGroup):
    get_category_name = State()


@dp.message_handler(state=MyForm.get_category_name)
async def process_category_name(message: types.Message, state: FSMContext):
    category_name = message.text
    if category_name == "⤴ Back":
        await dp.bot.send_message(message.chat.id, "🛑 Adding was canceled.", reply_markup=keyboards.admin_panel)
        await state.finish()
        return
    if db.add_category(category_name):
        await dp.bot.send_message(message.chat.id, f"Category '{category_name}' added successfully.")
    else:
        await dp.bot.send_message(message.chat.id, f"Failed to add category '{category_name}'. Try again.")
    await state.finish()


async def show_categories_for_deletion(message: types.Message):
    categories = db.get_all_categories()
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for category in categories:
        markup.add(types.KeyboardButton(category.name))
    markup.add(types.KeyboardButton("⤴ Back"))
    await dp.bot.send_message(message.chat.id, "Select a category to delete:", reply_markup=markup)
    await MyForm.get_category_name.set()


async def delete_product_command(message: types.Message):
    if message.from_user.id == admin_id:
        products = db.get_all_products()

        if not products:
            await dp.bot.send_message(message.chat.id, "No products available for deletion.")
            return

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        for product in products:
            markup.add(types.KeyboardButton(f"ID: {product.id}, Caption: {product.caption}, "
                                            f"Description: {product.description[:50]}.., Price: {product.price} ❌"))

        markup.add(types.KeyboardButton("⤴ Back"))
        await dp.bot.send_message(message.chat.id, "Select a product to delete:", reply_markup=markup)
        await MyForm.get_category_name.set()
    else:
        await dp.bot.send_message(message.chat.id, "You are not authorized to delete products.")


@dp.message_handler(state=MyForm.get_category_name)
async def process_delete_command(message: types.Message, state: FSMContext):
    if message.text.startswith("ID"):
        # Extract the product ID from the selected product text
        product_id = message.text.replace("ID: ", '').strip().split(',')[0]
        try:
            if product_id is not None:
                db.delete_product(product_id)
                await dp.bot.send_message(message.from_user.id, f"Product with ID {product_id} has been deleted.",
                                          reply_markup=keyboards.admin_panel)
            else:
                await dp.bot.send_message(message.from_user.id, "Invalid product selection.",
                                          reply_markup=keyboards.admin_panel)
        except Exception as e:
            await dp.bot.send_message(message.from_user.id, f"Error: {e}")
    elif message.text == "⤴ Back":
        await dp.bot.send_message(message.chat.id, "Operation canceled.")
    else:
        await dp.bot.send_message(message.chat.id, "Invalid selection.")


# ... (other handlers and code)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
