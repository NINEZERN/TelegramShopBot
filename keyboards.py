from telebot import types
import db

admin_panel = types.ReplyKeyboardMarkup(resize_keyboard=True)
admin_panel.add(types.KeyboardButton("➕ Add product"))
admin_panel.add(types.KeyboardButton("➕ Add category"))
admin_panel.add(types.KeyboardButton("❌ Delete product"))
admin_panel.add(types.KeyboardButton("❌ Delete category"))


# categories = types.ReplyKeyboardMarkup(resize_keyboard=True)

# for category in db.get_all_categories():
#     print (categories.add(category.name))



back_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
back_menu.add(types.KeyboardButton("⤴ Back"))

add_media_menu = types.ReplyKeyboardMarkup(resize_keyboard=True)
add_media_menu.add(types.KeyboardButton("📷 photo"))
add_media_menu.add(types.KeyboardButton("🎥 video"))


