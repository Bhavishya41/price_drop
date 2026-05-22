import os
import requests

# ==================== CONFIGURATION ====================
URL = "https://genesispc.in/products/mchose-g75-pro.json"
PRICE_FILE = "last_price.txt"

# Pulled from GitHub Repository Secrets / Environment
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin"
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
        
        if response.status_code == 403:
            print("❌ Cloudflare blocked the script (403). Session headers need adjustment.")
            return
        elif response.status_code != 200:
            print(f"❌ Failed to fetch product data. Status: {response.status_code}")
            return

        product_data = response.json().get("product", {})
        title = product_data.get("title", "MCHOSE G75 PRO Mechanical Keyboard")
        variants = product_data.get("variants", [])
        
        current_price = None
        variant_title = ""

        # Tier 1 Fallback: Direct hardware SKU matching (Highly preferred)
        for variant in variants:
            if variant.get("sku") == "G75-13A":
                price_str = variant.get("price").replace(",", "").strip()
                current_price = float(price_str)
                variant_title = variant.get("title", "")
                print("🎯 Target variant located via Primary SKU validation.")
                break

        # Tier 2 Fallback: If SKU matches nothing, drop down to text description mining
        if current_price is None:
            print("⚠️ SKU not found. Initializing Tier 2 text-matching fallback workflow...")
            for variant in variants:
                v_title = variant.get("title", "")
                if "Black" in v_title and "Matcha Latte" in v_title:
                    price_str = variant.get("price").replace(",", "").strip()
                    current_price = float(price_str)
                    variant_title = v_title
                    print("✅ Variant located via alternative text description mapping.")
                    break

        # Tier 3 Fallback: Safety baseline to prevent compilation crashes if inventory is wiped
        if current_price is None and variants:
            print("⚠️ All targeted matches exhausted. Defaulting to first available platform item entry.")
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
        
        res = requests.post(api_url, json=payload, timeout=10)
        if res.status_code != 200:
            print(f"Telegram API Error response status code: {res.text}")
            
    except Exception as e:
        print(f"Failed to transmit Telegram message packet: {e}")

if __name__ == "__main__":
    check_price()