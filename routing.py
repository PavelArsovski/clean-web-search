import subprocess
import time
import logging
import socket
import requests
from stem import Signal
from stem.control import Controller
from config import TOR_PATH, TORRC_PATH
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs.txt")
    ]
)
logging.getLogger("stem").setLevel(logging.ERROR)


class TorManager:
    def __init__(self):
        self.tor_process = None
        self.executor = ThreadPoolExecutor(max_workers=1)

    def is_tor_running(self) -> bool:
        """Check if the Tor subprocess is still running."""
        return self.tor_process is not None and self.tor_process.poll() is None

    def is_tor_port_open(self, host='127.0.0.1', port=9050, timeout=2):
        """Check if Tor is already running by testing if the SOCKS port is open."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            try:
                s.connect((host, port))
                return True
            except (ConnectionRefusedError, socket.timeout):
                return False

    def start_tor(self) -> bool:
        """Start the Tor process silently if not already running."""
        try:
            if self.is_tor_running():
                logging.info("Tor is already running.")
                return True

            logging.info("Starting Tor process...")
            self.tor_process = subprocess.Popen(
                [TOR_PATH, "-f", TORRC_PATH],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            for i in range(20):
                if self.tor_process.poll() is None:
                    time.sleep(0.5)
                else:
                    raise RuntimeError("Tor process exited prematurely.")

            logging.info("Tor started successfully.")
            return True

        except Exception as e:
            logging.error(f"Failed to start Tor: {e}")
            return False

    def stop_tor(self):
        """Terminate the Tor process gracefully."""
        if self.tor_process:
            try:
                logging.info("Stopping Tor process...")
                self.tor_process.terminate()
                self.tor_process.wait(timeout=10)
                logging.info("Tor stopped successfully.")
            except Exception as e:
                logging.warning(f"Failed to stop Tor cleanly: {e}")
            finally:
                self.tor_process = None

    def rotate_ip(self) -> bool:
        old_ip = self._get_current_ip()
        if old_ip is None:
            logging.error("Couldn't determine current IP")
            return False

        controller = None
        try:
            controller = Controller.from_port(port=9051)
            controller.authenticate(password="NAPISI SI GO TVOJO!!")
            controller.signal(Signal.NEWNYM)

            wait_time = controller.get_newnym_wait() or 5
            time.sleep(wait_time)

            new_ip = self._get_current_ip()
            if new_ip and new_ip != old_ip:
                logging.info(f"IP changed from {old_ip} to {new_ip}")
            else:
                logging.warning("IP did not change after rotation")

            time.sleep(1)
            return new_ip != old_ip

        except Exception as e:
            logging.error(f"IP rotation failed: {str(e)}")
            return False
        finally:
            if controller:
                try:
                    controller.close()
                except Exception as e:
                    logging.warning(f"Failed to close Tor controller: {e}")

    def rotate_ip_async(self):
        """Run rotate_ip() in the background using ThreadPoolExecutor."""
        self.executor.submit(self.rotate_ip)

    def _get_current_ip(self) -> str:
        """Get current external IP using Tor."""
        try:
            session = requests.Session()
            session.proxies = {
                'http': 'socks5h://127.0.0.1:9050',
                'https': 'socks5h://127.0.0.1:9050'
            }
            return session.get('https://api.ipify.org').text
        except Exception as e:
            logging.error(f"Failed to get current IP: {str(e)}")