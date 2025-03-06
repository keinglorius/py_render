import os
import cv2
import numpy as np
from skimage.morphology import skeletonize
import networkx as nx
import matplotlib.pyplot as plt
from scipy.interpolate import splprep, splev
import matplotlib.patches as patches
from scipy.spatial import Delaunay
from matplotlib.patches import PathPatch
from matplotlib.path import Path

def preprocess_image(input_path):
    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"❌ Không tìm thấy file: {input_path}")

    if img.shape[-1] == 4:
        alpha = img[:, :, 3]
        binary = np.where(alpha == 0, 0, 255).astype(np.uint8)
    else:
        binary = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(binary, 1, 255, cv2.THRESH_BINARY)

    return binary

def get_skeleton(input_path):
    binary = preprocess_image(input_path)
    binary[binary > 0] = 1  # Convert to binary 0-1
    binary = cv2.medianBlur(binary, 3)
    skeleton = skeletonize(binary)
    skeleton = (skeleton * 255).astype(np.uint8)
    return skeleton

def get_points_from_skeleton(skeleton):
    return np.column_stack(np.where(skeleton > 0))

def get_connected_paths(points, distance_threshold=2):
    G = nx.Graph()
    if len(points) < 3:
        return []

    tri = Delaunay(points)
    edges = set()
    for simplex in tri.simplices:
        for i in range(3):
            for j in range(i + 1, 3):
                p1, p2 = points[simplex[i]], points[simplex[j]]
                dist = np.linalg.norm(p1 - p2)
                if dist <= distance_threshold:
                    edges.add((tuple(p1), tuple(p2)))

    for edge in edges:
        G.add_edge(*edge, weight=np.linalg.norm(np.array(edge[0]) - np.array(edge[1])))

    mst = nx.minimum_spanning_tree(G)  # Dùng cây bao trùm nhỏ nhất để tránh nối xa
    paths = [list(comp) for comp in nx.connected_components(mst)]
    return paths

def smooth_path(path, smoothing_factor=3):
    path = np.array(path)
    if len(path) < 4:
        return path  # Không cần làm mịn nếu ít điểm
    tck, u = splprep([path[:, 0], path[:, 1]], s=smoothing_factor)
    new_points = splev(np.linspace(0, 1, len(path)), tck)
    return np.column_stack(new_points)

def save_paths_as_eps(paths, output_path):
    fig, ax = plt.subplots()
    for path in paths:
        smoothed = smooth_path(path)
        smoothed_path = Path(smoothed[:, [1, 0]])
        patch = PathPatch(smoothed_path, facecolor='none', edgecolor='black', lw=1)
        ax.add_patch(patch)
    ax.set_xlim(min(p[1] for path in paths for p in path), max(p[1] for path in paths for p in path))
    ax.set_ylim(min(-p[0] for path in paths for p in path), max(-p[0] for path in paths for p in path))
    ax.set_aspect('equal')
    ax.set_axis_off()
    plt.savefig(output_path, format='eps', bbox_inches='tight', pad_inches=0)
    plt.close(fig)

def main(input_path, output_eps):
    skeleton = get_skeleton(input_path)
    points = get_points_from_skeleton(skeleton)
    paths = get_connected_paths(points)

    plt.imshow(skeleton, cmap="gray")
    for path in paths:
        path = np.array(path)
        plt.scatter(path[:, 1], path[:, 0], s=1)
    plt.show()

    save_paths_as_eps(paths, output_eps)
    print(f'✅ Xuất file EPS thành công: {output_eps}')


# 🚀 Chạy chương trình
image = "outline"
input_path = f"image/{image}.png"
svg_path = f"image/export/{image}.eps"

main(input_path, svg_path)

