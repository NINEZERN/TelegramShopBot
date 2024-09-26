import logging
import telebot
from telebot import types
import time
from telebot.handler_backends import State, StatesGroup  # States
import db
import keyboards
import config
import sys

API_TOKEN = config.BOT_TOKEN  # Replace with your API token

# Initialize logger
logging.basicConfig(filename="bot.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

# Initialize bot
bot = telebot.TeleBot(API_TOKEN)

# Admin IDs (replace with your list of Telegram IDs)
admin_ids = config.ADMIN_IDS

# Initialize the database
db.init_database()

# Add categories (example)
db.add_category("📜 12 days shopping")
db.add_category("📜 5 days shopping")
db.add_category("📜 others")
db.add_category("🎧 Electronics")


def generate_category_keyboard():
    categories = types.ReplyKeyboardMarkup()
    for category in db.get_all_categories():
        categories.add(category.name)
    return categories


# Commands
@bot.message_handler(commands=['start'])
def start(message: types.Message):
    bot.send_message(message.chat.id, "😎Hello and welcome to our store!!!\n🛒Here all available categories:",
                     reply_markup=generate_category_keyboard())


@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id in admin_ids:
        bot.send_message(message.chat.id, "🎉 Welcome back sir", reply_markup=keyboards.admin_panel)
    else:
        bot.send_message(message.chat.id, "You are not authorized to access the admin panel.")


# Button handler
@bot.message_handler(content_types='text')
def buttons_handler(message):
    if message.text in [category.name for category in db.get_all_categories()]:
        logging.info(f"User {message.from_user.username} clicked {message.text}")
        products = db.get_products_by_category(message.text)
        if not products:
            bot.send_message(message.chat.id, "Seems like it`s nothing in there😢")
            return
        for product in products:
            if (product.media_type == "photo"):
                bot.send_photo(message.chat.id, product.media_id)
            else:
                bot.send_video(message.chat.id, product.media_id)
            bot.send_invoice(message.chat.id,
                             title=f"{product.caption.capitalize()}",
                             description=f"{product.description}",
                             provider_token=config.PAYMENT_TOKEN,
                             currency='USD',
                             prices=[types.LabeledPrice("Product", int(product.price) * 100)],
                             is_flexible=False,
                             need_email=True,
                             need_shipping_address=True,
                             start_parameter="minecraft_dota",
                             invoice_payload='payment_payload')

    if message.from_user.id in admin_ids:
        if message.text == "➕ Add product":
            bot.send_message(message.chat.id, 'Write a caption for your product.', reply_markup=keyboards.back_menu)
            bot.register_next_step_handler(message, get_caption)

        elif message.text == "❌ Delete product":
            delete_product_command(message)

        elif message.text == "⤴ Back":
            bot.send_message(message.chat.id, "👌 Back to menu", reply_markup=keyboards.admin_panel)

        elif message.text == "➕ Add category":
            bot.send_message(message.chat.id, "Write the name of the new category.")
            bot.register_next_step_handler(message, add_category)

        elif message.text == "❌ Delete category":
            bot.send_message(message.chat.id, "Select a category to delete.")
            show_categories(message)


# Function to show categories for selection
def show_categories(message):
    categories = db.get_all_categories()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for category in categories:
        markup.add(types.KeyboardButton(category.name))
    markup.add(types.KeyboardButton("⤴ Back"))
    bot.send_message(message.chat.id, "Select a category:", reply_markup=markup)
    bot.register_next_step_handler(message, process_category_selection)


# Function to handle category selection
def process_category_selection(message):
    if message.text == "⤴ Back":
        bot.send_message(message.chat.id, "Operation canceled.")
        return

    # Handle the selected category (e.g., delete it)
    category_name = message.text
    delete_category(message, category_name)


# Function to add a new category
def add_category(message):
    if message.text == "⤴ Back":
        bot.send_message(message.chat.id, "Operation canceled.")
        return

    category_name = message.text
    if db.add_category(category_name):
        bot.send_message(message.chat.id, f"Category '{category_name}' added successfully.")
    else:
        bot.send_message(message.chat.id, f"Failed to add category '{category_name}'. Try again.")


# Function to delete a category
def delete_category(message, category_name):
    logging.info(f"Category {category_name} deleted")

    # Retrieve all products in the category
    products_in_category = db.get_products_by_category(category_name.strip())

    # Delete each product in the category
    for product in products_in_category:
        db.delete_product(product.id)

    # Now, delete the category
    db.delete_category(category_name.strip())
    bot.send_message(message.chat.id, f"Category '{category_name.strip()}' and its associated products deleted successfully.",
                     reply_markup=keyboards.admin_panel)


# Payment
@bot.shipping_query_handler(func=lambda query: True)
def shipping(shipping_query):
    logging.info(shipping_query)
    bot.answer_shipping_query(shipping_query.id, ok=True,
                              error_message='Oh, seems like our Dog couriers are having a lunch right now. Try again later!')


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Aliens tried to steal your card's CVV, but we successfully protected your credentials,"
                                                " try to pay again in a few minutes, we need a small rest.")


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message: types.Message):

    payment_info = message.successful_payment
    # Send message for user
    bot.send_message(message.chat.id,
                     'Hoooooray! Thanks for payment! We will proceed your order for `{} {}` as fast as possible! '
                     'Stay in touch and write to our admin: @{} If you have any questions'.format(
                         payment_info.total_amount / 100,
                         payment_info.currency, bot.get_chat(admin_ids[0]).username),
                     parse_mode='Markdown')

    # Send message for admin
    formatted_message = f"🛑 WE GOT PAYMENT 💸\n"\
                        f"<b>User:</b> @{message.from_user.username}\n"\
                        f"<b>Email:</b> {payment_info.order_info.email}\n"\
                        f"<b>Address:</b> {payment_info.order_info.shipping_address}\n"\
                        f"<b>Total Amount:</b> ${payment_info.total_amount / 100:.2f}"

    bot.send_message(message.chat.id, formatted_message, parse_mode='HTML')
    logging.info(f"User: @{message.from_user.username}\n"\
                        f"Email: {payment_info.order_info.email}\n"\
                        f"Address: {payment_info.order_info.shipping_address}\n"\
                        f"Total Amount: ${payment_info.total_amount / 100:.2f}")


# Delete product
def delete_product_command(message):
    if message.from_user.id in admin_ids:
        products = db.get_all_products()

        if not products:
            bot.send_message(message.chat.id, "No products available for deletion.")
            return

        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)

        for product in products:
            markup.add(
                telebot.types.KeyboardButton(
                    f"ID: {product.id}, Caption: {product.caption}, Description: {product.description[:50]}.., Price: {product.price} ❌"))

        markup.add(telebot.types.KeyboardButton("⤴ Back"))
        bot.send_message(message.chat.id, "Select a product to delete:", reply_markup=markup)
        bot.register_next_step_handler(message, process_delete_command)
    else:
        bot.send_message(message.chat.id, "You are not authorized to delete products.")


def process_delete_command(message):
    if message.text.startswith("ID"):
        # Extract the product ID from the selected product text
        product_id = message.text.replace("ID: ", '').strip().split(',')[0]
        try:
            if product_id is not None:

                # Now you can use the product_id to delete the corresponding product
                db.delete_product(product_id)
                bot.send_message(message.from_user.id, f"Product with ID {product_id} has been deleted.",
                                 reply_markup=keyboards.admin_panel)
                logging.info(f"Product with ID {product_id} has been deleted")
            else:
                bot.send_message(message.from_user.id, "Invalid product selection.", reply_markup=keyboards.admin_panel)
        except Exception as e:
            bot.send_message(message.from_user.id, f"Error: {e}")
    elif message.text == "⤴ Back":
        bot.send_message(message.chat.id, "Operation canceled.")
    else:
        bot.send_message(message.chat.id, "Invalid selection.")


# Add product
def get_caption(message):
    if message.text == "⤴ Back":
        bot.send_message(message.chat.id, "🛑 Adding was canceled.", reply_markup=keyboards.admin_panel)
        bot.delete_state(message.from_user.id, message.chat.id)
        return

    # Check if the caption is not empty and is a valid string
    if not message.text or not isinstance(message.text, str):
        bot.send_message(message.chat.id, '👀 Please enter a valid caption for your product.',
                         reply_markup=keyboards.admin_panel)
        return

    caption = message.text
    bot.send_message(message.chat.id, 'Write a description for your product.')
    bot.register_next_step_handler(message, get_description, caption)


def get_description(message, caption):
    if message.text == "⤴ Back":
        bot.send_message(message.chat.id, "🛑 Adding was canceled.", reply_markup=keyboards.admin_panel)
        bot.delete_state(message.from_user.id, message.chat.id)
        return

    # Check if the description is not empty and is a valid string
    if not message.text or not isinstance(message.text, str):
        bot.send_message(message.chat.id, '👀 Please enter a valid description for your product.',
                         reply_markup=keyboards.admin_panel)
        return

    description = message.text
    bot.send_message(message.chat.id, 'Write the price for your product.')
    bot.register_next_step_handler(message, get_price, caption, description)


def get_price(message, caption, description):
    if message.text == "⤴ Back":
        bot.send_message(message.chat.id, "🛑 Adding was canceled.", reply_markup=keyboards.admin_panel)
        bot.delete_state(message.from_user.id, message.chat.id)
        return

    # Check if the price is a valid number
    try:
        price = float(message.text)
    except ValueError:
        bot.send_message(message.chat.id, '👀 Please enter a valid number for the price.',
                         reply_markup=keyboards.admin_panel)
        return

    bot.send_message(message.chat.id, 'What would you like to add, a photo or a video?',
                     reply_markup=keyboards.add_media_menu)

    # Save the caption, description, and price in the user_data
    user_data = {'caption': caption, 'description': description, 'price': price}
    bot.register_next_step_handler(message, get_media_type, user_data)


def get_media_type(message, user_data):
    if message.text == "⤴ Back":
        bot.send_message(message.chat.id, "🛑 Adding was canceled.", reply_markup=keyboards.admin_panel)
        bot.delete_state(message.from_user.id, message.chat.id)
        return
    if message.text.lower() == "📷 photo":
        bot.send_message(message.chat.id, 'Send a photo for your product.', reply_markup=keyboards.back_menu)
        user_data['media_type'] = 'photo'
        bot.register_next_step_handler(message, get_media, user_data)
    elif message.text.lower() == "🎥 video":
        bot.send_message(message.chat.id, 'Send a video for your product.', reply_markup=keyboards.back_menu)
        user_data['media_type'] = 'video'
        bot.register_next_step_handler(message, get_media, user_data)
    else:
        bot.send_message(message.chat.id, 'Invalid choice. Please select either "photo" or "video".',
                         reply_markup=keyboards.admin_panel)


def get_media(message, user_data):
    if message.text == "⤴ Back":
        bot.send_message(message.chat.id, "🛑 Adding was canceled.", reply_markup=keyboards.admin_panel)
        bot.delete_state(message.from_user.id, message.chat.id)
        return
    if user_data['media_type'] == 'photo' and message.photo:
        media_id = message.photo[-1].file_id
        user_data['media_id'] = media_id
        bot.send_message(message.chat.id, 'Select a category for your product:',
                         reply_markup=generate_category_keyboard())
        bot.register_next_step_handler(message, get_category, user_data)
    elif user_data['media_type'] == 'video' and message.video:
        media_id = message.video.file_id
        user_data['media_id'] = media_id
        bot.send_message(message.chat.id, 'Select a category for your product:',
                         reply_markup=generate_category_keyboard())
        bot.register_next_step_handler(message, get_category, user_data)
    else:
        bot.send_message(message.chat.id, f'No {user_data["media_type"]} received. Please try again.',
                         reply_markup=keyboards.admin_panel)


def get_category(message, user_data):
    if message.text == "⤴ Back":
        bot.send_message(message.chat.id, "🛑 Adding was canceled.", reply_markup=keyboards.admin_panel)
        bot.delete_state(message.from_user.id, message.chat.id)
        return
    category = message.text
    db.add_product(user_data['caption'], user_data['description'], user_data['price'], user_data['media_type'],
                   user_data['media_id'], category)

    bot.send_message(
        message.chat.id,
        f"✔ Product {user_data['caption']} has been added successfully with the {user_data['media_type']} in category: {category}",
        reply_markup=keyboards.back_menu)
    # Depending on your design, you may want to provide more feedback or options to the user.


if __name__ == '__main__':
    while True:
        try:
            print ("Bot is running")
            bot.polling(none_stop=True)

        except Exception as e:
            logging.error(e)
            time.sleep(15)
        