import numpy as np
import cv2
import glob
from fileio import FileSaver

chessboard_size = (9, 6) 
chessboard_height = 9
chessboard_width = 6

channels = 3


obj_points = []  # 3D
img_points = []  # 2D

objp = np.zeros((chessboard_height * chessboard_width, channels), np.float32)
objp[:, :2] = np.mgrid[0:chessboard_height, 0:chessboard_width].T.reshape(-1, 2)

image_files = glob.glob('calibration-frames/*.jpg')

for image_file in image_files:
    print(image_file)
    img = cv2.imread(image_file)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    ret, corners = cv2.findChessboardCorners(gray, chessboard_size, None)

    if ret:
        obj_points.append(objp)
        img_points.append(corners)
    else: print("Failed to recognize corner in file", image_file)


ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points, gray.shape[::-1], None, None)


fs = FileSaver(root="calibration/", inline=False)

data = {
    "matrix" : camera_matrix.tolist(),
    "distortion" : dist_coeffs.tolist()
}

file_name = fs.save_file("calibration", data)

print("Saved data to", file_name)