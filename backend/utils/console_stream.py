import asyncio
import sys
from io import StringIO
from fastapi import WebSocket
import logging

class ConsoleStreamCapture:
    def __init__(self):
        self.buffer = StringIO()
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def start(self):
        sys.stdout = self
        sys.stderr = self

    def stop(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

    def write(self, data):
        self.buffer.write(data)
        self.buffer.flush()  # Ensuring data is written immediately

    def flush(self):
        pass

    def get_output(self):
        output = self.buffer.getvalue()
        self.buffer.truncate(0)
        self.buffer.seek(0)
        return output

console_capture = ConsoleStreamCapture()

async def start_console_stream_server(websocket: WebSocket, model_id: str, action: str):
    await websocket.accept()
    
    try:
        console_capture.start()
        logging.basicConfig(stream=sys.stdout, level=logging.INFO, force=True)

        task_complete = False
        while True:
            output = console_capture.get_output()
            if output:
                await websocket.send_text(output)
                # Ensuring every piece of the output is processed
                logging.info(f"Processing output: {output}")
                if "Completed response: 200" in output or "failed" in output or "Error:" in output:
                    task_complete = True
                    # Send a final "Task Completed" message
                    await websocket.send_text("Task Completed")
                    break
            await asyncio.sleep(0.1)

    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        console_capture.stop()
        try:
            await websocket.close()
        except RuntimeError:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("console_stream:app", host="0.0.0.0", port=8000, log_level="debug", reload=True)
