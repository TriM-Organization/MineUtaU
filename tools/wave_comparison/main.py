import librosa
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import faiss

import time
import sys
import os

using_gpu = False


def extract_features(file_path):
    """
    特征提取与融合函数
    """
    try:
        y, sr = librosa.load(file_path, sr=None)

        # MFCC (13 维)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1)

        # Chroma (12 维)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr).mean(axis=1)

        # Zero Crossing Rate (1 维)
        zcr = librosa.feature.zero_crossing_rate(y).mean()

        # 合并成一个特征向量
        features = np.hstack([mfcc, chroma, zcr])
        return features
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


from pathlib import Path


def load_all_features(directory, max_workers=8):
    # 并行提取音频特征
    files = list(Path(directory).glob("*.wav"))
    features = []
    paths = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(extract_features, map(str, files)))

    for file, feat in zip(files, results):
        if feat is not None:
            features.append(feat)
            paths.append(str(file))

    return paths, np.array(features)


def build_faiss_index(features, use_gpu=True):
    """
    构建 FAISS 索引
    """
    dimension = features.shape[1]
    index = faiss.IndexFlatL2(dimension)

    if use_gpu:
        res = faiss.StandardGpuResources()
        index = faiss.index_cpu_to_gpu(res, 0, index)

    index.add(len(features), features)
    return index


def find_best_matches(group_a_paths, group_a_features, group_b_paths, group_b_features, use_gpu=True):
    """
    寻找最佳匹配
    """
    index = build_faiss_index(group_b_features, use_gpu=use_gpu)

    # 这一行代码有问题啊
    D, I = index.search(len(group_a_features), group_a_features, k=1)  # 每个 A 只找最像的 B

    results = []
    for i, (dist, idx) in enumerate(zip(D, I)):
        a_path = group_a_paths[i]
        b_path = group_b_paths[idx[0]]
        similarity = 1 / (1 + dist[0])  # 转换为相似度分数 [0~1]
        results.append((a_path, b_path, similarity))

    return results



if __name__ == "__main__":

    group_a_dir = "audio_data/group_a"
    group_b_dir = "audio_data/group_b"

    print("从 甲 组中提取声音特征信息")
    start = time.time()
    group_a_paths, group_a_features = load_all_features(group_a_dir)
    print(f"完成 {len(group_a_paths)} 个文件，耗时 {time.time() - start:.2f} 秒")

    print("从 乙 组中提取声音特征信息")
    start = time.time()
    group_b_paths, group_b_features = load_all_features(group_b_dir)
    print(f"完成 {len(group_b_paths)} 个文件，耗时 {time.time() - start:.2f} 秒")

    print("查找匹配中")
    results = find_best_matches(group_a_paths, group_a_features, group_b_paths, group_b_features)

    print("\n匹配结果如下：")
    for a, b, score in results:
        print(f"{os.path.basename(a)} -> {os.path.basename(b)} (score: {score:.4f})")