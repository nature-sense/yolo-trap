import os
import cv2
import numpy as np

from datetime import datetime
from libcamera import controls
from picamera2 import Picamera2, MappedArray
from ultralytics import YOLO

class CacheEntry:
    def __init__(self, session, track_id, score):
        current_datetime = datetime.now()
        current_timestamp_ms = int(current_datetime.timestamp() * 1000)
        self.session = session
        self.created = current_timestamp_ms
        self.updated = current_timestamp_ms
        self.track_id = track_id
        self.score = score

    def update(self, score):
        current_datetime = datetime.now()
        save_image =  score > self.score
        self.score = score
        self.updated = int(current_datetime.timestamp() * 1000)
        return save_image

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

class Session :
    def __init__(self, size, directory):
        self.cache = FixedSizeMap(size)
        now = datetime.now()
        self.session = now.strftime("%Y%d%m%H%M%S")

        self.session_dir = f"{directory}/{self.session}"
        self.image_dir = f"{self.session_dir}/images"
        self.metadata_dir = f"{self.session_dir}/metadata"
        os.mkdir(self.session_dir)
        os.mkdir(self.image_dir)
        os.mkdir(self.metadata_dir)

    def save_image(self, track_id, img):
        cv2.imwrite(f"{self.image_dir}/{track_id : 06d}.jpg", img)


class DetectFlow:

    def __init__(self, max_tracking, min_score, sessions_directory, lores_size, main_size, model):
        os.environ['LIBCAMERA_LOG_LEVELS'] = '4'
        self.picam2 = Picamera2()
        self.session = Session(max_tracking, sessions_directory)
        self.model = YOLO(model)
        self.min_score = min_score
        self.lores_size = lores_size
        self.main_size = main_size

    def flow_task(self):
        camera_config = self.picam2.create_preview_configuration(
            main={'format': 'RGB888', 'size': self.main_size},
            lores={'format': 'RGB888', 'size': self.lores_size}
        )

        self.picam2.configure(camera_config)
        self.picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0})  # 2.0})
        self.picam2.start()

        while True:
            job = self.picam2.capture_request(wait=False)
            

            request = self.picam2.capture_request()

            with MappedArray(request, 'lores') as l:
                results = self.model.track(l.array)

                current_datetime = datetime.now()
                #current_timestamp_ms = int(current_datetime.timestamp() * 1000)

                boxes = results[0].boxes.xyxy.cpu().numpy().astype(np.int32)
                track_ids = results[0].boxes.id.int().cpu().numpy().astype(np.int32)
                scores = results[0].boxes.conf.numpy()
                classes = results[0].boxes.cls.numpy().astype(np.int32)
                annotated_frame = results[0].plot()
                cv2.imwrite("img.jpg", annotated_frame)

                with (MappedArray(request, 'main') as m):
                    for box, track_id, score, clazz in zip(boxes, track_ids, scores, classes):
                        # print("timestamp", current_timestamp_ms)
                        # print("box", box)
                        # print("track-id", track_id)
                        # print("score", score)
                        # print("class", clazz)

                        save_image = False
                        cache_entry = self.session.cache.get(track_id)
                        if cache_entry is None:
                            if score > self.min_score:
                                cache_entry = CacheEntry(self.session.session, track_id, score)
                                self.session.cache.add(track_id, cache_entry)
                                save_image = True
                        else:
                            save_image = cache_entry.update(score)

                        if save_image:
                            scaled_box = self.scale(box)
                            # print("scaled-box", scaled_box)
                            x0, y0, x1, y1 = scaled_box
                            crop = m.array[y0:y1, x0:x1]
                            self.session.save_image(track_id, crop)
                            # cv2.imwrite(f"crop{track_id}.jpg", crop)
                request.release()

                # cv2.imshow("Camera", annotated_frame)

                # results = ncnn_model.track(source = m.array, stream=True, persist=True)
                # for r in results:
            #    print(r.boxes)

    def scale(self, rect):
        # multiprocessing.get_context().prec=1
        s_w, s_h = self.lores_size
        d_w, d_h = self.main_size
        x0, y0, x1, y1 = rect
        x_scale = d_w / s_w
        y_scale = d_h / s_h
        return int(x0 * x_scale), int(y0 * y_scale), int(x1 * x_scale), int(y1 * y_scale)


