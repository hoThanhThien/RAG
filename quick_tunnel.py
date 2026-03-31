import subprocess
import re
import time
import os

def start_tunnel_and_get_url():
    """Start Cloudflare tunnel and extract URL"""
    print("🚀 Starting Cloudflare Tunnel...")
    print("⏳ Please wait 10-15 seconds...")
    
    # Start tunnel
    process = subprocess.Popen([
        'cloudflared', 'tunnel', '--url', 'http://localhost:8000'
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    
    tunnel_url = None
    
    # Read output line by line to find URL
    try:
        while True:
            line = process.stdout.readline()
            if not line:
                break
                
            print(f"   {line.strip()}")
            
            # Look for the tunnel URL
            if "trycloudflare.com" in line and "Visit it at" in line:
                # Extract URL using regex
                url_match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if url_match:
                    tunnel_url = url_match.group(0)
                    break
                    
            # Alternative pattern
            elif "trycloudflare.com" in line:
                url_match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                if url_match:
                    tunnel_url = url_match.group(0)
                    break
                    
    except KeyboardInterrupt:
        print("\n🛑 Stopping tunnel...")
        process.terminate()
        return None, None
    
    return tunnel_url, process

def update_env_file(tunnel_url):
    """Update .env file with new webhook URL"""
    env_path = "backend/.env"
    webhook_url = f"{tunnel_url}/payments/webhook/bank"
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the BANK_WEBHOOK_URL line
        new_content = re.sub(
            r'BANK_WEBHOOK_URL=.*',
            f'BANK_WEBHOOK_URL={webhook_url}',
            content
        )
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Updated backend/.env with: {webhook_url}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update .env file: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🎯 CLOUDFLARE TUNNEL AUTO SETUP")
    print("=" * 60)
    
    # Start tunnel and get URL
    tunnel_url, tunnel_process = start_tunnel_and_get_url()
    
    if tunnel_url:
        webhook_url = f"{tunnel_url}/payments/webhook/bank"
        
        print("\n" + "=" * 60)
        print("🎉 SUCCESS! TUNNEL IS READY!")
        print("=" * 60)
        print(f"🌐 Tunnel URL: {tunnel_url}")
        print(f"🔗 Webhook URL: {webhook_url}")
        print("=" * 60)
        
        # Update .env file
        if update_env_file(tunnel_url):
            print("✅ Backend configuration updated!")
        
        print("\n📋 NEXT STEPS:")
        print("1. 🔗 Copy this URL:", webhook_url)
        print("2. 🌐 Go to: https://my.sepay.vn")
        print("3. ⚙️  Navigate to: Settings → Webhook")
        print("4. 📝 Paste the webhook URL")
        print("5. 💾 Save settings")
        
        print("\n⚠️  IMPORTANT:")
        print("• Keep this terminal window open")  
        print("• Tunnel will stop if you close this window")
        print("• Press Ctrl+C to stop tunnel")
        
        print(f"\n🧪 TEST YOUR WEBHOOK:")
        print(f"   curl {tunnel_url}/health")
        print(f"   curl {tunnel_url}/payments/debug/bank-txns")
        
        # Keep tunnel running
        try:
            print("\n🔄 Tunnel is running... Press Ctrl+C to stop")
            tunnel_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping tunnel...")
            tunnel_process.terminate()
            print("✅ Tunnel stopped. Goodbye!")
            
    else:
        print("\n❌ Failed to start tunnel or extract URL")
        print("💡 Try running manually: cloudflared tunnel --url http://localhost:8000")

if __name__ == "__main__":
    main()