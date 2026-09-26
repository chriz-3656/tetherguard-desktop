import cv2
from pathlib import Path
from datetime import datetime
import base64
from typing import Optional

class CameraResponder:
    def __init__(self, save_dir: Path):
        self.save_dir = save_dir
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def capture(self) -> Optional[str]:
        """
        Captures a single frame, saves it to disk, and returns the base64 encoded image.
        Returns None if capture fails.
        """
        try:
            # 0 is usually the default built-in webcam
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("Failed to open camera.")
                return None
            
            # Allow camera to warm up
            for _ in range(5):
                cap.read()
                
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                print("Failed to read frame.")
                return None
                
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = self.save_dir / f"capture_{timestamp}.jpg"
            
            cv2.imwrite(str(filename), frame)
            
            # Encode for websocket transmission
            _, buffer = cv2.imencode('.jpg', frame)
            b64_img = base64.b64encode(buffer).decode('utf-8')
            
            return b64_img
            
        except Exception as e:
            print(f"Camera capture error: {e}")
            return None
