import os
import time
from datetime import datetime

import cv2
import numpy as np
from libcamera import controls
from picamera2 import Picamera2, MappedArray
from ultralytics import YOLO

SESSIONS_DIRECTORY = "./sessions"
MAX_TRACKING = 10

class CacheEntry:
    def __init__(self, session, track_id):
        current_datetime = datetime.now()
        current_timestamp_ms = int(current_datetime.timestamp() * 1000)
        self.session = session
        self.created = current_timestamp_ms
        self.updated = current_timestamp_ms
        self.track_id = track_id


class FixedSizeMap:
    def __init__(self, capacity):
        self.capacity = capacity
        self.map = {}
        self.keys = []

    def add(self, key, value):
        if key in self.map:
            self.map[key] = value
            self.keys.remove(key)
            self.keys.append(key)
        else:
            if len(self.map) >= self.capacity:
                oldest_key = self.keys.pop(0)
                del self.map[oldest_key]
            self.map[key] = value
            self.keys.append(key)

    def get(self, key):
        return self.map.get(key)

    def remove(self, key):
      if key in self.map:
        del self.map[key]
        self.keys.remove(key)

    def __len__(self):
        return len(self.map)

'''
'''

class Session :
    def __init__(self):
        self.cache = FixedSizeMap(MAX_TRACKING)
        now = datetime.now()
        self.session = now.strftime("%Y%d%m%H%M%S")

        self.session_dir = f"{SESSIONS_DIRECTORY}/{self.session}"
        self.image_dir = f"{self.session_dir}/images"
        self.metadata_dir = f"{self.session_dir}/metadata"
        os.mkdir(self.session_dir)
        os.mkdir(self.image_dir)
        os.mkdir(self.metadata_dir)

    def detection(self, tracking_id, score, clazz, img):
        yield

if __name__ == "__main__":

    session = Session()

    picam2 = Picamera2()
    camera_config = picam2.create_preview_configuration(
        main={'format': 'RGB888', 'size': (2028, 1520)},
        lores={'format': 'RGB888', 'size': (320, 320)}
    )

    picam2.configure(camera_config)
    picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 2.0})

    #ncnn_model = YOLO("model/best_ncnn_model", task='detect')
    model = YOLO("model/best.pt")

    #picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
    picam2.start()
    while True:
        frame = picam2.capture_array()

        request = picam2.capture_request()
        with (MappedArray(request, 'lores') as l):
            results = model.track(l.array)

            current_datetime = datetime.now()
            current_timestamp_ms = int(current_datetime.timestamp() * 1000)

            boxes = results[0].boxes.xywh.cpu().numpy().astype(np.int32)
            track_ids = results[0].boxes.id.int().cpu().numpy().astype(np.int32)
            scores = results[0].boxes.conf.numpy()
            classes = results[0].boxes.cls.numpy().astype(np.int32)

            with (MappedArray(request, 'main') as m):
                for box, track_id, score, clazz in zip(boxes, track_ids, scores, classes):
                    print("timestamp", current_timestamp_ms)
                    print("box", box)
                    print("track-id", track_id)
                    print("score", score)
                    print("class", clazz)



            annotated_frame = results[0].plot()
            #cv2.imshow("Camera", annotated_frame)

            #results = ncnn_model.track(source = m.array, stream=True, persist=True)
            #for r in results:
            #    print(r.boxes)
            cv2.imwrite("img.jpg", annotated_frame)
        request.release()

