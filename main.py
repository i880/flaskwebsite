from flask import Flask, render_template, Response,jsonify,request
import cv2
import mediapipe as mp
import numpy as np
from playsound import playsound

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

app = Flask(__name__)

# Initialize the webcam (0 is the default camera)
camera = None
camera_active = None



def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radius = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radius * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle

    return angle

camera_active = False  # Default state
counter = 0
series = 0
stage = None
numbre_series = 0  # To be set dynamically from user input
numbre_heps = 0    # To be set dynamically from user input



def start_camera():
    global camera,camera_active
    if not camera_active:
        camera = cv2.VideoCapture(0)
        camera_active = True

def stop_camera():
    global camera_active,camera
    if camera_active == True:
        camera.release()
        camera_active=False

def generate_frames():
    global camera, camera_active, counter, series, stage, numbre_series, numbre_heps
    cap = cv2.VideoCapture(0)
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        playsound("/home/i880/Downloads/gooo-83817.mp3")
        while camera_active:
            ret, frame = cap.read()
            if not ret:
                break
            
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            result = pose.process(image)
            
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            try:
                landmarks = result.pose_landmarks.landmark
                shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

                angle = calculate_angle(shoulder, elbow, wrist)
                cv2.putText(image, str(int(angle)),
                            tuple(np.multiply(elbow, [640, 480]).astype(int)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 2, cv2.LINE_AA)

                if angle > 140:
                    stage = "DOWN"
                if angle < 50 and stage == "DOWN":
                    stage = "UP"
                    counter += 1

            except:
                pass

            # Update text on the frame
            cv2.rectangle(image, (0, 0), (100, 500), (245, 117, 60), -1)
            cv2.putText(image, 'HEPS', (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
            cv2.putText(image, str(counter), (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (200, 200, 200), 2, cv2.LINE_AA)
            cv2.putText(image, 'SERIES', (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
            cv2.putText(image, str(series), (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 2, (200, 200, 200), 2, cv2.LINE_AA)
            cv2.putText(image, stage, (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 2, cv2.LINE_AA)
            cv2.putText(image, "Reset: r ", (20, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

            mp_drawing.draw_landmarks(image, result.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                      mp_drawing.DrawingSpec(color=(0, 117, 77), thickness=2, circle_radius=2),
                                      mp_drawing.DrawingSpec(color=(245, 20, 0), thickness=2, circle_radius=2))

            if counter == numbre_heps:
                counter = 0
                series += 1
            if series == numbre_series:
                print("Exercise finished: good job")
                playsound("/home/i880/Downloads/he-is-good-133293.mp3")
                break

            ret, buffer = cv2.imencode('.jpg', image)
            image = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + image + b'\r\n')

    cap.release()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/feed')
def feed():
    return render_template('feed.html')

@app.route('/video_feed')
def video_feed():
    if not camera_active :
        return "camera not active" , 404
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/toggle_camera', methods=['POST'])
def toggle_camera():
    global camera_active, numbre_series, numbre_heps
    if not camera_active:
        data = request.json
        numbre_series = int(data.get('numSeries', 1))
        numbre_heps = int(data.get('numReps', 1))
        camera_active = True
        return jsonify({"status": "started"})
    else:
        camera_active = False
        return jsonify({"status": "stopped"})

if __name__ == "__main__":
    app.run(debug=True)