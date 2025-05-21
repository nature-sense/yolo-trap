
import asyncio
from concurrent.futures import ThreadPoolExecutor

from detect_flow import DetectFlow
from src.bluetooth_control import BluetoothControl

MODEL = "/home/yolodev/yolo-trap/model/best.pt"
SESSIONS_DIRECTORY = "./sessions"
MAX_TRACKING = 10
MIN_SCORE = 0.5

MAIN_SIZE = (2028, 1520)
LORES_SIZE = (320,320)

async def main() :


    detect_flow = DetectFlow(
        max_tracking=10,
        min_score = 0.5,
        sessions_directory = SESSIONS_DIRECTORY,
        lores_size = LORES_SIZE,
        main_size = MAIN_SIZE,
        model=MODEL
    )
    bluetooth_control = BluetoothControl(detect_flow)
    #flow = loop.run_in_executor(executor, detect_flow.flow_task)
    await bluetooth_control.run()
    #await asyncio.gather(flow, control)
    print("exit")

asyncio.run(main())