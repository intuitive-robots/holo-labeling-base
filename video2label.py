import cv2
import numpy as np
from scipy.spatial.transform import Rotation
import json, yaml
from fileio import read_yaml
    

def detect_qr_from_one_image(image, qr_detector: cv2.QRCodeDetector, cmtx, dist, qr_size=0.05):

    ret_qr, points = qr_detector.detect(image)
    if not ret_qr: return None, None, None


    qr_edges = np.array([[0, 0, 0],
                         [0, 1, 0],
                         [1, 1, 0],
                         [1, 0, 0]], dtype=np.float32).reshape((4, 1, 3)) * qr_size # why the reshape


    return cv2.solvePnP(qr_edges, points, cmtx, dist)


def unity2robot(a : np.array) -> np.array:
    return np.array([a[0], a[2], a[1], a[3], a[5], a[4], a[6], a[7], a[9], a[8]])

def generate_bbox_vertices_camera(bbox_3d):

    rotation = Rotation.from_quat(bbox_3d[3:7])

    bbox3d_vertices = np.array([
        [bbox_3d[-3], bbox_3d[-2], bbox_3d[-1]],
        [bbox_3d[-3], bbox_3d[-2], -bbox_3d[-1]],
        [bbox_3d[-3], -bbox_3d[-2], -bbox_3d[-1]],
        [bbox_3d[-3], -bbox_3d[-2], bbox_3d[-1]],
        [-bbox_3d[-3], bbox_3d[-2], bbox_3d[-1]],
        [-bbox_3d[-3], bbox_3d[-2], -bbox_3d[-1]],
        [-bbox_3d[-3], -bbox_3d[-2], -bbox_3d[-1]],
        [-bbox_3d[-3], -bbox_3d[-2], bbox_3d[-1]],
    ]) * 0.5

    for i, vertex in enumerate(bbox3d_vertices):
        bbox3d_vertices[i] = np.array(bbox_3d[:3]) + rotation.apply(vertex)
    return bbox3d_vertices

def generate_bbox_edge_image(bbox2d_vertices):
    edges = []
    
    for i in range(3):
        edges.append([bbox2d_vertices[i], bbox2d_vertices[i + 1]])
        edges.append([bbox2d_vertices[i + 4], bbox2d_vertices[i + 5]])

    edges.append([bbox2d_vertices[0], bbox2d_vertices[3]])
    edges.append([bbox2d_vertices[4], bbox2d_vertices[-1]])
    
    for i in range(4):
        edges.append([bbox2d_vertices[i], bbox2d_vertices[i + 4]])
    
    return edges

def draw_bbox_from_3d(image, bbox_3d, rvec, tvec, cmtx, dist, color=(0, 0,0)):

    bbox_3d_vertices = generate_bbox_vertices_camera(bbox_3d)
    bbox_2d_vertices, _ = cv2.projectPoints(bbox_3d_vertices, rvec, tvec, cmtx, dist)
    bbox_2d_vertices = np.round(bbox_2d_vertices).astype(np.int32)
    bbox_2d_vertices = bbox_2d_vertices.reshape((8, 2))
    
    bbox_2d_edges = generate_bbox_edge_image(bbox_2d_vertices)

    for edge in bbox_2d_edges:
        cv2.line(image, edge[0], edge[1], color, 4)


def from_cam(cap: cv2.VideoCapture, qr_detector: cv2.QRCodeDetector, cmtx, dist, data : dict, capture : bool = False):

    bboxes = [unity2robot(box["pos"] + box["rot"] + box["scale"]) for box in data.values()]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    writer = None
    if capture:
        img_width, img_height = int(cap.get(3)), int(cap.get(4))
        writer = cv2.VideoWriter("output.mp4", fourcc, 20.0, (img_width, img_height))


    if not cap.isOpened: 
        print("Invalid video file specified")

    index = 0
    while True:
        ret, img = cap.read()
        if not ret: break


        # preprocess the image 
        grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # grey scale
        thres = cv2.threshold(grey, 255, cv2.THRESH_BINARY, 11) 

        ret, rvec, tvec = detect_qr_from_one_image(grey, qr_detector, cmtx, dist)
        
        if ret: 
            for data in bboxes:
                draw_bbox_from_3d(img, data, rvec, tvec, cmtx, dist)
            cv2.imwrite(f'imgs/frame{index}.png', img) 
            index += 1


        cv2.imshow('thres', img)

        if writer: writer.write(img)

        k = cv2.waitKey(20)
        if k == 27: break #27 is ESC key.
        
    cap.release()
    if writer: writer.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":


    
    conf  = read_yaml("conf.yaml") # general config

    content = read_yaml(conf["calibration_file"]) # camera calibration data 
    cmtx, dist = np.array(content["matrix"]), np.array(content["distortion"])

    meta_file = read_yaml(conf["saves_meta"]) # saves meta file for last upload
    select_save = conf["select_save"]

    save = read_yaml(select_save) if len(select_save) > 0 else read_yaml(meta_file["latest_file"]) # if no save was selected use last uploaded save 
    
    cap = cv2.VideoCapture(conf["video_path"]) # video file to use 
    from_cam(cap, cv2.QRCodeDetector(), cmtx, dist, save)