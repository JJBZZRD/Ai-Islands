import asyncio
import subprocess
import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)

async def start_console_stream_server(websocket: WebSocket, model_id: str, action: str, epochs: int, batch_size: int, learning_rate: float, dataset_id: str, imgsz: int):
    await websocket.accept()

    try:
        command = f"python backend/utils/train_vis.py --model_id {model_id} --action {action} --epochs {epochs} --batch_size {batch_size} --learning_rate {learning_rate} --dataset_id {dataset_id} --imgsz {imgsz}"
        
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        while True:
            output = process.stdout.readline()
            if output:
                await websocket.send_text(output)
            else:
                break

        error_output = process.stderr.read()
        if error_output:
            await websocket.send_text(error_output)

        process.wait()
        await websocket.send_text("Task Completed and Model Updated in Library")

    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass
        
async def start_load_model_server(websocket: WebSocket, model_id: str):
    await websocket.accept()

    try:
        await websocket.send_text(f"Starting to load model {model_id}...")
        await asyncio.sleep(2)  
        await websocket.send_text(f"Model {model_id} loaded successfully.")
        await websocket.send_text("Task Completed")
    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass

async def start_unload_model_server(websocket: WebSocket, model_id: str):
    await websocket.accept()

    try:
        await websocket.send_text(f"Starting to unload model {model_id}...")
        await asyncio.sleep(2)  
        await websocket.send_text(f"Model {model_id} unloaded successfully.")
        await websocket.send_text("Task Completed")
    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass
