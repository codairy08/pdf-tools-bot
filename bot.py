import logging
import os
import asyncio
from telegram import Update, InputFile, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext
from PyPDF2 import PdfMerger
from PIL import Image

TOKEN = "7926041099:AAEHE-dy5S5TD8cmxUcR2Fd78Bs4_smDw0Q"

# Configure logging
logging.basicConfig(level=logging.INFO)

# Dictionary to store user PDFs for merging
user_pdfs = {}

# Start Command
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("📷 Convert Image to PDF", callback_data="convert_pdf")],
        [InlineKeyboardButton("📑 Merge PDFs", callback_data="merge_pdf")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help"), InlineKeyboardButton("❓ About", callback_data="about")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📄 Welcome to PDF Tools Bot!\n\n"
        "Choose an option below to get started:",
        reply_markup=reply_markup
    )

# Handle Button Clicks
async def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()  # Acknowledge the button press

    if query.data == "convert_pdf":
        await query.message.reply_text("📸 Send me an image, and I'll convert it to a PDF.")
    elif query.data == "merge_pdf":
        await query.message.reply_text("📑 Send multiple PDFs one by one. Type /done when finished.")
        user_pdfs[query.message.chat_id] = []  # Initialize user session
    elif query.data == "help":
        await query.message.reply_text(
            "🛠 **How to Use This Bot:**\n"
            "1️⃣ Send an **image**, and I'll convert it to a PDF.\n"
            "2️⃣ Send multiple **PDFs**, and I'll merge them into one (use /done when finished)."
        )
    elif query.data == "about":
        await query.message.reply_text("ℹ️ **PDF Tools Bot**\nCreated to help you with PDF tasks! 🚀")

# Convert Image to PDF
async def image_to_pdf(update: Update, context: CallbackContext) -> None:
    processing_message = await update.message.reply_text("⏳ Processing... 0%")
    
    # Download the image
    photo = await update.message.photo[-1].get_file()
    file_path = "input.jpg"
    await photo.download_to_drive(file_path)
    
    await asyncio.sleep(1)
    await processing_message.edit_text("⏳ Processing... 50%")

    # Convert to PDF
    image = Image.open(file_path).convert('RGB')
    pdf_path = "output.pdf"
    image.save(pdf_path)

    await asyncio.sleep(1)
    await processing_message.edit_text("✅ Processing Complete! Sending PDF... 100%")

    # Send PDF
    with open(pdf_path, "rb") as pdf_file:
        await update.message.reply_document(document=InputFile(pdf_file, filename="converted.pdf"))
    
    # Cleanup
    os.remove(file_path)
    os.remove(pdf_path)

# Store PDF files for merging
async def receive_pdf(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    if user_id not in user_pdfs:
        await update.message.reply_text("⚠️ Please press '📑 Merge PDFs' first before sending files!")
        return

    pdf_file = await update.message.document.get_file()
    file_path = f"temp_{len(user_pdfs[user_id])}.pdf"
    await pdf_file.download_to_drive(file_path)

    user_pdfs[user_id].append(file_path)
    await update.message.reply_text(f"✅ PDF {len(user_pdfs[user_id])} saved! Send more or type /done.")

# Merge PDFs
async def merge_pdfs(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    if user_id not in user_pdfs or len(user_pdfs[user_id]) < 2:
        await update.message.reply_text("⚠️ Please send at least **two PDFs** before merging!")
        return

    processing_message = await update.message.reply_text("⏳ Merging PDFs...")

    merger = PdfMerger()
    for pdf in user_pdfs[user_id]:
        merger.append(pdf)

    output_path = "merged.pdf"
    merger.write(output_path)
    merger.close()

    await processing_message.edit_text("✅ Merging Complete! Sending PDF...")

    with open(output_path, "rb") as pdf_file:
        await update.message.reply_document(document=InputFile(pdf_file, filename="merged.pdf"))

    # Cleanup
    for pdf in user_pdfs[user_id]:
        os.remove(pdf)
    os.remove(output_path)

    del user_pdfs[user_id]  # Reset user session

# Main Function
def main():
    app = Application.builder().token(TOKEN).read_timeout(30).write_timeout(30).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.PHOTO, image_to_pdf))
    app.add_handler(MessageHandler(filters.Document.PDF, receive_pdf))
    app.add_handler(CommandHandler("done", merge_pdfs))
    
    app.run_polling()

if __name__ == '__main__':
    main()
