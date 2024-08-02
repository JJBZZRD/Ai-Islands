import asyncio
import websockets
import cv2
import json

async def send_video(video_path, uri, frame_interval=120, resize_factor=0.5):
    async with websockets.connect(uri) as websocket:
        cap = cv2.VideoCapture(video_path)
        frame_count = 0

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                # Skip frames based on the interval
                if frame_count % frame_interval != 0:
                    continue

                # Resize frame
                frame = cv2.resize(frame, (0, 0), fx=resize_factor, fy=resize_factor)

                # Encode frame as JPG
                _, buffer = cv2.imencode('.jpg', frame)
                data = buffer.tobytes()

                try:
                    # Send the frame to the server
                    await websocket.send(data)
                    print("Frame sent")

                    # Receive the prediction from the server
                    prediction = await websocket.recv()
                    print("Prediction received:", json.loads(prediction))
                except websockets.exceptions.ConnectionClosed as e:
                    print(f"Connection closed with exception: {e}")
                    break

        except Exception as e:
            print(f"Error during video processing: {e}")
        finally:
            cap.release()
            try:
                await websocket.close()
            except Exception as close_exception:
                print(f"Error closing websocket: {close_exception}")

if __name__ == "__main__":
    import sys
    video_path = sys.argv[1]
    uri = sys.argv[2]
    asyncio.run(send_video(video_path, uri, frame_interval=2, resize_factor=0.5))  # The frame interval can be adjusted as needed, it is predefined like this for now

# For testing
"""python websocket_client.py "path to vid file" ws://localhost:8000/ws/predict-live/modelname"""
