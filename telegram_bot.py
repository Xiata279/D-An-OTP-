import telebot
import threading
import time

class Spambot:
    def __init__(self, token, start_callback, stop_callback, status_callback):
        self.bot = telebot.TeleBot(token)
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.status_callback = status_callback
        self.is_running = True

        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            chat_id = message.chat.id
            self.bot.reply_to(message, f"🤖 **LUÂN EM C2 BOT**\n\n🆔 **CHAT ID CỦA BẠN:** `{chat_id}`\n(Hãy copy ID này nhập vào Tool để nhận thông báo)\n\n📜 **Lệnh:**\n/attack [sđt] - Tấn công ngay\n/stop - Dừng lại\n/status - Xem trạng thái")

        @self.bot.message_handler(commands=['attack'])
        def handle_attack(message):
            try:
                args = message.text.split()
                if len(args) < 2:
                    self.bot.reply_to(message, "❌ Thiếu số điện thoại!\nVí dụ: /attack 0901234567")
                    return
                phone = args[1]
                # Default settings for Telegram attack
                result = self.start_callback(phone, 2.0, 5, [], 'carpet') 
                self.bot.reply_to(message, f"🚀 {result['message']}")
            except Exception as e:
                self.bot.reply_to(message, f"❌ Lỗi: {str(e)}")

        @self.bot.message_handler(commands=['stop'])
        def handle_stop(message):
            result = self.stop_callback()
            self.bot.reply_to(message, f"🛑 {result['message']}")

        @self.bot.message_handler(commands=['status'])
        def handle_status(message):
            stats = self.status_callback()
            msg = f"📊 **THỐNG KÊ**\n\n" \
                  f"🔥 Đã gửi: {stats['sent']}\n" \
                  f"✅ Thành công: {stats['success']}\n" \
                  f"❌ Thất bại: {stats['fail']}\n" \
                  f"🧵 Luồng: {stats['threads']}\n" \
                  f"🛡️ Trạng thái: {'ĐANG CHẠY' if stats['running'] else 'ĐÃ DỪNG'}"
            self.bot.reply_to(message, msg)

    def start(self):
        print("Telegram Bot Started...")
        self.bot.infinity_polling()

    def send_message(self, chat_id, text):
        try:
            self.bot.send_message(chat_id, text)
        except Exception as e:
            print(f"Telegram Send Error: {e}")
