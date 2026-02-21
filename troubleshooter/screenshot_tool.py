import base64
from io import BytesIO
from PIL import ImageGrab

def capture_screen_base64() -> str:
    """Captures the screen and returns a base64 encoded string of the image."""
    try:
        screenshot = ImageGrab.grab()
        buffered = BytesIO()
        screenshot.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return img_str
    except Exception as e:
        print(f"Error capturing screen: {e}")
        return None
