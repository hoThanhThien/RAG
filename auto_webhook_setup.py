import requests
import subprocess
import re
import time
import os
from dotenv import load_dotenv

load_dotenv()

def get_tunnel_url():
    """Start cloudflare tunnel and extract URL"""
    print("🚀 Starting Cloudflare Tunnel...")
    
    # Start tunnel in background
    process = subprocess.Popen([
        'cloudflared', 'tunnel', '--url', 'http://localhost:8000'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for tunnel to start and capture output
    time.sleep(10)
    
    # Read output to find URL
    output = ""
    while True:
        line = process.stdout.readline()
        if not line:
            break
        output += line
        print(line.strip())
        
        # Look for tunnel URL
        if "trycloudflare.com" in line:
            url_match = re.search(r'https://[^.]+\.trycloudflare\.com', line)
            if url_match:
                tunnel_url = url_match.group(0)
                print(f"✅ Tunnel URL found: {tunnel_url}")
                return tunnel_url, process
    
    return None, process

def update_sepay_webhook(webhook_url):
    """Update SePay webhook URL via API"""
    
    # Try different possible SePay API endpoints and methods
    SEPAY_WEBHOOK_SECRET = os.getenv('SEPAY_WEBHOOK_SECRET')
    SEPAY_ACCOUNT_NUMBER = "0375227764"
    
    if not SEPAY_WEBHOOK_SECRET:
        print("❌ SEPAY_WEBHOOK_SECRET not found in .env file")
        return False
    
    print("🔍 Attempting to find SePay API for webhook update...")
    
    # Method 1: Try with webhook secret as API key
    api_endpoints = [
        "https://my.sepay.vn/userapi/bank/webhook",
        "https://my.sepay.vn/api/v1/bank/webhook", 
        "https://sepay.vn/api/webhook/update",
        "https://api.sepay.vn/v1/webhook"
    ]
    
    headers_variants = [
        {'Authorization': f'Bearer {SEPAY_WEBHOOK_SECRET}', 'Content-Type': 'application/json'},
        {'X-API-KEY': SEPAY_WEBHOOK_SECRET, 'Content-Type': 'application/json'},
        {'Authorization': SEPAY_WEBHOOK_SECRET, 'Content-Type': 'application/json'}
    ]
    
    data_variants = [
        {'account_number': SEPAY_ACCOUNT_NUMBER, 'webhook_url': f"{webhook_url}/payments/webhook/bank"},
        {'bank_account': SEPAY_ACCOUNT_NUMBER, 'webhook': f"{webhook_url}/payments/webhook/bank"},
        {'webhook_url': f"{webhook_url}/payments/webhook/bank"}
    ]
    
    for api_url in api_endpoints:
        for headers in headers_variants:
            for data in data_variants:
                try:
                    print(f"🔄 Trying: {api_url}")
                    response = requests.post(api_url, headers=headers, json=data, timeout=10)
                    
                    print(f"   Status: {response.status_code}")
                    print(f"   Response: {response.text[:200]}...")
                    
                    if response.status_code in [200, 201]:
                        print(f"✅ SUCCESS! SePay webhook updated via: {api_url}")
                        return True
                        
                except Exception as e:
                    print(f"   Error: {str(e)}")
                    continue
    
    print("❌ Could not find working SePay API endpoint")
    print("💡 You may need to update webhook manually in SePay dashboard")
    print(f"   Webhook URL to use: {webhook_url}/payments/webhook/bank")
    return False

def update_env_file(webhook_url):
    """Update .env file with new webhook URL"""
    env_path = "backend/.env"
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Replace webhook URL
    new_content = re.sub(
        r'BANK_WEBHOOK_URL=.*',
        f'BANK_WEBHOOK_URL={webhook_url}/payments/webhook/bank',
        content
    )
    
    with open(env_path, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Updated .env file with new webhook URL")

def main():
    print("🎯 Starting Auto Webhook Update System...")
    
    # Get tunnel URL
    tunnel_url, tunnel_process = get_tunnel_url()
    
    if not tunnel_url:
        print("❌ Failed to get tunnel URL")
        return
    
    # Update .env file
    update_env_file(tunnel_url)
    
    # Update SePay webhook
    if update_sepay_webhook(tunnel_url):
        print("\n🎉 SUCCESS! Everything is set up:")
        print(f"   🌐 Tunnel URL: {tunnel_url}")
        print(f"   🔗 Webhook URL: {tunnel_url}/payments/webhook/bank")
        print("\n⚠️  Keep this script running to maintain the tunnel!")
        
        # Keep tunnel running
        try:
            tunnel_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping tunnel...")
            tunnel_process.terminate()
    else:
        print("❌ Failed to update SePay webhook")
        tunnel_process.terminate()

if __name__ == "__main__":
    main()