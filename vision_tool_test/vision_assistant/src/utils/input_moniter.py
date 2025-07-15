from pynput import mouse, keyboard
from datetime import datetime
import json
import threading
import os

class InputMonitor:
    def __init__(self, log_file="input_events.json"):
        self.log_file = log_file
        self.events = []
        self.running = False
        self.lock = threading.Lock()
        self.current_section = 0  # Track current section number
        
        # Keyboard state tracking
        self.pressed_keys = set()
        self.modifier_keys = {'Key.ctrl', 'Key.shift', 'Key.alt', 'Key.cmd', 'Key.ctrl_l', 'Key.ctrl_r', 
                            'Key.shift_l', 'Key.shift_r', 'Key.alt_l', 'Key.alt_r', 'Key.cmd_l', 'Key.cmd_r'}
        self.sustained_modifiers = set()
        
        # Special key mapping for better readability
        self.special_key_mapping = {
            'Key.page_up': 'PageUp',
            'Key.page_down': 'PageDown',
            'Key.caps_lock': 'CapsLock',
            'Key.num_lock': 'NumLock',
            'Key.scroll_lock': 'ScrollLock',
            'Key.insert': 'Insert',
            'Key.delete': 'Delete',
            'Key.home': 'Home',
            'Key.end': 'End',
            'Key.print_screen': 'PrintScreen',
            'Key.pause': 'Pause',
            'Key.backspace': 'Backspace',
            'Key.enter': 'Enter',
            'Key.esc': 'Esc',
            'Key.tab': 'Tab',
            'Key.space': 'Space',
            'Key.up': '↑',
            'Key.down': '↓',
            'Key.left': '←',
            'Key.right': '→',
        }
        # Add F1-F12 keys to the mapping
        for i in range(1, 13):
            self.special_key_mapping[f'Key.f{i}'] = f'F{i}'
        
    def start(self):
        """Start monitoring mouse and keyboard events."""
        self.running = True
        
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        
        self.mouse_listener = mouse.Listener(
            on_move=None,  # Ignore mouse movement
            on_click=self._on_mouse_click,
            on_scroll=None  # Ignore scroll events
        )
        
        self.keyboard_listener.start()
        self.mouse_listener.start()
        
        # Start first section
        self._start_new_section()
        
        print("Input monitoring started. Press Ctrl+C to stop.")
        print("Press Cmd + Shift (⌘ + ⇧) or Ctrl + Shift to start a new section in the log.")
        
    def stop(self):
        """Stop monitoring and save the collected events."""
        self.running = False
        self.keyboard_listener.stop()
        self.mouse_listener.stop()
        self.save_events()
        print("\nInput monitoring stopped. Events saved to", self.log_file)
        
    def _start_new_section(self):
        """Start a new section in the log."""
        self.current_section += 1
        self._add_event('section', {
            'action': 'start',
            'section_number': self.current_section
        })
    
    def _add_event(self, event_type, details):
        """Add an event to the events list with timestamp and section."""
        if not self.running:
            return
            
        event = {
            'timestamp': datetime.now().isoformat(),
            'section': self.current_section,
            'type': event_type,
            'details': details
        }
        
        with self.lock:
            self.events.append(event)
    
    def _normalize_key(self, key):
        """Normalize key name for consistent representation."""
        try:
            # Handle regular character keys
            if hasattr(key, 'char') and key.char:
                return key.char
                
            # Convert key to string
            key_str = str(key)
            
            # Handle special keys
            if key_str in self.special_key_mapping:
                return self.special_key_mapping[key_str]
                
            # Handle modifier keys
            if key_str in self.modifier_keys:
                base_key = key_str.split('_')[0]  # Remove _l or _r suffix
                return base_key
                
            # Default case
            return key_str
            
        except AttributeError:
            return str(key)
    
    def _is_modifier_key(self, key_str):
        """Check if a key is a modifier key."""
        return key_str in self.modifier_keys
    
    def is_section_hotkey(self):
        """Check if current modifier combination is for section marking."""
        modifiers = set(str(key) for key in self.pressed_keys)
        # Check for Cmd/Ctrl + Shift
        return (('Key.shift' in modifiers or 'Key.shift_l' in modifiers or 'Key.shift_r' in modifiers) and
                ('Key.ctrl' in modifiers or 'Key.ctrl_l' in modifiers or 'Key.ctrl_r' in modifiers or
                 'Key.cmd' in modifiers or 'Key.cmd_l' in modifiers or 'Key.cmd_r' in modifiers))

    def _on_key_press(self, key):
        """Handle keyboard press events."""
        key_str = self._normalize_key(key)
        
        # Add to pressed keys set
        self.pressed_keys.add(str(key))  # Store original key string
        
        # If it's a modifier key, add to sustained modifiers
        if self._is_modifier_key(str(key)):
            self.sustained_modifiers.add(key_str)
            # Check for section marker after adding the modifier
            if self.is_section_hotkey():
                self._start_new_section()
                print("You've started a new section.")
            return
        
        # Add to pressed keys set
        if key_str not in self.pressed_keys:
            self.pressed_keys.add(str(key))
        
        # If there are sustained modifiers, this is part of a hotkey
        if self.sustained_modifiers:
            hotkey_keys = list(self.sustained_modifiers) + [key_str]
            hotkey = '+'.join(sorted(set(hotkey_keys)))
            self._add_event('keyboard', {
                'action': 'hotkey',
                'combination': hotkey
            })
        else:
            # This is a regular key press without modifiers
            self._add_event('keyboard', {
                'action': 'press',
                'key': key_str
            })
    
    def _on_key_release(self, key):
        """Handle keyboard release events."""
        key_str = self._normalize_key(key)
        
        # Remove the original key string from pressed keys
        self.pressed_keys.discard(str(key))
        
        # If it's a modifier key, remove from sustained modifiers
        if self._is_modifier_key(str(key)):
            self.sustained_modifiers.discard(key_str)
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click events."""
        if pressed:
            self._add_event('mouse', {
                'action': 'click',
                'button': str(button),
                'position': {'x': x, 'y': y}
            })
    
    def save_events(self):
        """Save collected events to the log file, grouped by sections."""
        with self.lock:
            # Create a structured format with sections
            structured_log = {
                'total_sections': self.current_section,
                'sections': {}
            }
            
            # Group events by section
            for event in self.events:
                section_num = event['section']
                # Remove section from event since it's now in the structure
                event_copy = event.copy()
                del event_copy['section']
                
                # Initialize section if not exists
                if section_num not in structured_log['sections']:
                    structured_log['sections'][section_num] = []
                
                # Add event to appropriate section
                structured_log['sections'][section_num].append(event_copy)
            
            # Save to file with pretty printing
            with open(self.log_file, 'w') as f:
                json.dump(structured_log, f, indent=2)
    
    def get_events(self):
        """Return the current list of events."""
        with self.lock:
            return self.events.copy()

def main():
    """Main function to demonstrate usage."""
    try:
        monitor = InputMonitor()
        monitor.start()
        
        while True:
            pass
            
    except KeyboardInterrupt:
        monitor.stop()

if __name__ == "__main__":
    main()