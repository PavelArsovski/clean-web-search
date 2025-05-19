from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from routing import TorManager
import time

def launch_clean_gmail_signup():
    options = Options()

    # Route traffic through Tor
    options.set_preference("network.proxy.type", 1)
    options.set_preference("network.proxy.socks", "127.0.0.1")
    options.set_preference("network.proxy.socks_port", 9050)
    options.set_preference("network.proxy.socks_remote_dns", True)

    # Private session, clear data
    options.set_preference("browser.privatebrowsing.autostart", True)
    options.set_preference("privacy.clearOnShutdown.cookies", True)
    options.set_preference("privacy.clearOnShutdown.cache", True)
    options.set_preference("places.history.enabled", False)
    options.set_preference("signon.rememberSignons", False)

    # Speed up browser
    options.set_preference("startup.homepage_welcome_url", "about:blank")
    options.set_preference("browser.newtabpage.enabled", False)

    # Start browser
    driver = webdriver.Firefox(options=options)
    driver.get("https://www.google.com")

if __name__ == "__main__":
    tor = TorManager()
    
    if tor.start_tor():
        if tor.rotate_ip():  # Ensures a new IP
            print("[✓] Tor started and IP rotated.")
        else:
            print("[!] Failed to rotate IP.")

        launch_clean_gmail_signup()
        
        # Optional: Stop Tor after automation
        time.sleep(10)
        tor.stop_tor()
    else:
        print("[!] Failed to start Tor.")