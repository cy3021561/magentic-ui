import platform
from urllib.parse import urlparse
import requests
import json
import time

if platform.system() == 'Windows':
    import win32gui
    import win32process
    import psutil

class WindowTracker:
    def __init__(self):
        self.browser_processes = ['chrome', 'firefox', 'msedge', 'brave', 'safari']
        self.system = platform.system()
        self.last_title = None
        self.last_status = None

    def get_active_window(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            
            return {
                'title': win32gui.GetWindowText(hwnd),
                'process_name': process.name().lower().replace('.exe', ''),
                'pid': pid,
                'is_browser': process.name().lower().replace('.exe', '') in self.browser_processes
            }
        except Exception as e:
            return {'error': str(e)}

    def get_chrome_tabs(self):
        try:
            response = requests.get('http://127.0.0.1:9222/json')
            return response.json()
        except Exception as e:
            print(f"Error getting tabs: {str(e)}")
            return []

    def get_tab_load_status(self, tab_id):
        """Get the page load status for a specific tab"""
        try:
            # Make a request to the tab's debug URL
            response = requests.get(f'http://127.0.0.1:9222/json/list')
            tabs = response.json()
            
            for tab in tabs:
                if tab.get('id') == tab_id:
                    # Check if the tab is still loading
                    return not tab.get('loading', False)
                    
            return False
        except Exception as e:
            print(f"Error getting load status: {str(e)}")
            return False

    def get_active_tab_info(self):
        try:
            active_window = self.get_active_window()
            if not active_window.get('is_browser'):
                return None

            window_title = active_window['title']
            
            # Get all tabs
            tabs = self.get_chrome_tabs()
            
            # Find the tab that matches the window title
            for tab in tabs:
                if tab['type'] == 'page':
                    tab_title = tab['title']
                    
                    if window_title.startswith(tab_title):
                        # Get load status
                        is_loaded = self.get_tab_load_status(tab['id'])
                        
                        return {
                            'url': tab['url'],
                            'title': tab['title'],
                            'domain': urlparse(tab['url']).netloc,
                            'is_loaded': is_loaded,
                            'id': tab['id']
                        }
            
            return None
            
        except Exception as e:
            print(f"Error getting tab info: {str(e)}")
            return None

    def check_connection(self):
        try:
            response = requests.get('http://127.0.0.1:9222/json/version')
            return response.status_code == 200
        except:
            return False

if __name__ == "__main__":
    tracker = WindowTracker()
    
    try:
        print("Active Tab Tracker Started. Press Ctrl+C to exit.")
        print("Make sure Chrome is running with --remote-debugging-port=9222")
        
        if not tracker.check_connection():
            print("Failed to connect to Chrome debugging port. Exiting...")
            exit(1)
            
        print("Successfully connected to Chrome")
        print("Monitoring for active tab changes and load status...")
        
        while True:
            if not tracker.check_connection():
                print("Lost connection to Chrome. Waiting for reconnection...")
                time.sleep(2)
                continue
            
            tab_info = tracker.get_active_tab_info()
            if tab_info:
                current_state = f"{tab_info['title']}:{tab_info['is_loaded']}"
                print("!"*20)
                print(current_state)
                print("!"*20)
                if not tab_info['is_loaded']:
                    exit()
                # if current_state != tracker.last_status:
                #     print("\n" + "="*50)
                #     print(f"Tab Status Update:")
                #     print(f"Title: {tab_info['title']}")
                #     print(f"URL: {tab_info['url']}")
                #     print(f"Domain: {tab_info['domain']}")
                #     print(f"Loaded: {tab_info['is_loaded']}")
                tracker.last_status = current_state
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nStopping tracker...")
        print("Tracker stopped.")
    except Exception as e:
        print(f"Error: {str(e)}")