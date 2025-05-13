# Yolo-Trap

Yolo-Trap is an expermental AI insect-trap which uses Raspberry-Pi hardwareaand a  custom-trained Yolo11n model to detect and capture images of insects .

The trap is based on the concepts and training data from this project:

[Sittinger M, Uhler J, Pink M, Herz A (2024) Insect detect: An open-source DIY camera trap for automated insect monitoring. PLOS ONE 19(4): e0295474](https://doi.org/10.1371/journal.pone.0295474)

This project uses a relatively expensive [Luxonis OAK-1 AI camera,](https://shop.luxonis.com/products/oak-1?variant=42664380334303) whereas the Yolo-Trap project uses a stardard [Raspberry Pi camera](https://www.raspberrypi.com/documentation/accessories/camera.html), and runs the detection model on the Raspberry Pi itself, the aim being to provide a more cost effective solution.

## Architecture



![architecture](images/architecture.png)

  

## Session

The Yolo-Trap organises captured data into sessions. A session contains the set of data captured in a continuous period. 

A session is defined by a session_id which is the timestamp when the capture started. It has the format  YYYYMMDDHHMMSS

e.g

`20251205045854`



## Data Organisation

Session data is organised according to the following directory structure:

<img src="images/session.png" alt="session" style="zoom:50%;" />

Each session has its own directory with two subdirectories:

- images - containing the cropped insect images for offline inference.
- metadata - one file per image containg the image's metadata (see below)

## Tracking

