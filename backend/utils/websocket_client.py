import asyncio
import websockets
import cv2
import json

async def send_video(video_path, uri):
    async with websockets.connect(uri) as websocket:
        cap = cv2.VideoCapture(video_path)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            data = buffer.tobytes()

            # Send the frame to the server
            await websocket.send(data)
            print("Frame sent")  # Debug statement

            # Receive the prediction from the server
            prediction = await websocket.recv()
            print("Prediction received:", json.loads(prediction))  # Debug statement

        cap.release()    

if __name__ == "__main__":
    import sys
    video_path = sys.argv[1]
    uri = sys.argv[2]
    asyncio.run(send_video(video_path, uri))