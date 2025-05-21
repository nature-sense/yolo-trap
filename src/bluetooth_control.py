import asyncio
import logging
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Any

from bless import (  # type: ignore
    BlessServer,
    BlessGATTCharacteristic,
    GATTCharacteristicProperties,
    GATTAttributePermissions,
)

SERVICE_UUID    = "213e313b-d0df-4350-8e5d-ae657962bb56"
STATE_UUID      = "f4a6c1ed-86ff-4c01-932f-7c810dc66b43"

class BluetoothControl :
    def __init__(self, flow):
        self.executor = ThreadPoolExecutor()
        self.loop = asyncio.get_running_loop()
        self.trigger = asyncio.Event()
        self.flow = flow
        self.captureThread = None

        self.active = False

        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(name=__name__)

    def read_request(self,characteristic: BlessGATTCharacteristic, **kwargs) -> bytearray:
        self.logger.debug(f"Reading {characteristic.value}")
        return characteristic.value


    def write_request(self, characteristic: BlessGATTCharacteristic, value: Any, **kwargs):
        if characteristic.uuid == STATE_UUID:
            characteristic.value = value
            state = characteristic.value[0] == 1
            self.logger.debug(f"State set to {characteristic.value} {state}")
            if state is True and self.captureThread is None :
                self.logger.debug("Starting capture thread")
                self.captureThread = self.loop.run_in_executor(self.executor, self.flow.flow_task)
            elif state is False and self.captureThread is not None:
                self.logger.debug("Stopping capture thread")
                self.captureThread.cancel()
                self.captureThread = None

        #if characteristic.value == b"\x01":
        #    self.logger.debug("NICE")
        #    self.trigger.set()

    async def run(self):
        self.trigger.clear()
        # Instantiate the server
        service_name = "YOLO TRAP"
        server = BlessServer(name= service_name, loop=self.loop)
        server.read_request_func = self.read_request
        server.write_request_func = self.write_request

        # Add Service
        await server.add_new_service(SERVICE_UUID)

        # Add a Characteristic to the service
        char_flags = (
            GATTCharacteristicProperties.read
            | GATTCharacteristicProperties.write
            | GATTCharacteristicProperties.indicate
        )
        permissions = GATTAttributePermissions.readable | GATTAttributePermissions.writeable
        await server.add_new_characteristic(
            service_uuid = SERVICE_UUID,
            char_uuid=STATE_UUID,
            properties = char_flags,
            value= bytearray(1),
            permissions=permissions
        )
        await server.start()

        self.logger.debug("Advertising")
        await self.trigger.wait()


    #await asyncio.sleep(2)
    #logger.debug("Updating")
    #server.get_characteristic(my_char_uuid)
    #server.update_value(my_service_uuid, "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B")
    #await asyncio.sleep(5)
    #await server.stop()

