import os
import requests

# ==================== CONFIGURATION ====================
# Updated directly for the VXE Dragonfly R1 JSON endpoint
URL = "https://www.genesispc.in/products/vxe-dragonfly-r1.json"
PRICE_FILE = "last_price_mouse.txt"  # Separate tracking file for the mouse history

# Pulled from your existing GitHub Repository Secrets
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}
# =======================================================

def get_last_price():
    if not os.path.exists(PRICE_FILE):
        return None
    with open(PRICE_FILE, "r") as f:
        try:
            return float(f.read().strip())
        except ValueError:
            return None

def save_current_price(price):
    with open(PRICE_FILE, "w") as f:
        f.write(str(price))

def check_price():
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch mouse data. Status: {response.status_code}")
            return

        product_data = response.json().get("product", {})
        title = product_data.get("title", "VXE Dragonfly R1 Wireless Mouse")
        variants = product_data.get("variants", [])
        
        current_price = None
        variant_title = ""

        # Tier 1 Fallback: Direct hardware SKU matching from your new screenshot
        for variant in variants:
            if variant.get("sku") == "6976742070042":
                price_str = variant.get("price").replace(",", "").strip()
                current_price = float(price_str)
                variant_title = variant.get("title", "")
                print("🎯 Target mouse variant located via Primary SKU validation.")
                break

        # Tier 2 Fallback: Drop down to text descriptive string mining if the SKU updates
        if current_price is None:
            print("⚠️ Mouse SKU not found. Initializing Tier 2 text fallback...")
            for variant in variants:
                v_title = variant.get("title", "")
                if "R1" in v_title and "White" in v_title:
                    price_str = variant.get("price").replace(",", "").strip()
                    current_price = float(price_str)
                    variant_title = v_title
                    print("✅ Mouse variant located via text description mapping.")
                    break

        # Tier 3 Fallback: Baseline safety default
        if current_price is None and variants:
            print("⚠️ All targeted matches exhausted. Defaulting to first available mouse model entry.")
            first_variant = variants[0]
            price_str = first_variant.get("price", "0").replace(",", "").strip()
            current_price = float(price_str)
            variant_title = first_variant.get("title", "Default Variant")

        if current_price is None:
            print("❌ Error: No product variants could be pulled from the store data package.")
            return

        full_product_name = f"{title} ({variant_title})"
        last_price = get_last_price()
        
        print(f"📦 Product: {full_product_name}")
        print(f"💰 Current Price: ₹{current_price} | Previous Price: {f'₹{last_price}' if last_price else 'None'}")

        if last_price is not None and current_price < last_price:
            send_telegram_message(full_product_name, current_price, last_price)
            print("📉 Price drop detected! Telegram notification dispatched.")
        elif last_price is None:
            print("✅ First run initialized successfully. Baseline tracking price recorded.")
        else:
            print("➖ No price alterations detected on this interval check.")

        save_current_price(current_price)
            
    except Exception as e:
        print(f"An unexpected script parsing error occurred: {e}")

def send_telegram_message(product_title, new_price, old_price):
    try:
        savings = round(old_price - new_price, 2)
        clean_purchase_url = URL.replace(".json", "")
        
        message = (
            f"📉 *Price Drop Alert!*\n\n"
            f"📦 *Product:* {product_title}\n"
            f"💰 *Old Price:* ₹{old_price}\n"
            f"🔥 *New Price:* ₹{new_price} (Saved ₹{savings}!)\n\n"
            f"🔗 [Buy it on GenesisPC]({clean_purchase_url})"
        )
        
        api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        requests.post(api_url, json=payload, timeout=10)
            
    except Exception as e:
        print(f"Failed to transmit Telegram message packet: {e}")

if __name__ == "__main__":
    check_price()