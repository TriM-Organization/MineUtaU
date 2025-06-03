from mpi4py import MPI
import os
import json
import fsb5
from io import BytesIO
import sys

# 初始化 MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# 主进程读取 JSON 并分发任务
if rank == 0:
    print("载入 sound_definitions.json 定义文件")

    # 加载 JSON 配置
    with open("sounds/sound_definitions.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    sound_definitions = data.get("sound_definitions", {})

    # 构建任务列表：(sound_name, full_path)
    tasks = []
    for sound_name, entry in sound_definitions.items():
        sounds_list = entry.get("sounds", [])
        for item in sounds_list:
            if isinstance(item, dict):
                file_path = item.get("name")
            else:
                file_path = item
            full_path = os.path.join("sounds", file_path + ".fsb")
            tasks.append((sound_name, full_path))

    # 分发任务给各个进程
    chunks = [tasks[i::size] for i in range(size)]
else:
    chunks = None

# 各进程接收自己的任务
local_tasks = comm.scatter(chunks, root=0)

print(f"[任务 {rank}] 正在解析 {len(local_tasks)} 个文件...")

# 处理本地任务
for sound_name, fsb_file in local_tasks:
    if not os.path.isfile(fsb_file):
        print(f"[任务 {rank}] 无法找到文件: {fsb_file}")
        continue

    try:
        with open(fsb_file, "rb") as f:
            fsb_data = BytesIO(f.read())
            fsb = fsb5.FSB5(fsb_data)

        ext = fsb.get_sample_extension()
        output_path = os.path.join("output", f"{sound_name}.wav")

        # 合并所有样本为一个 WAV 文件
        all_samples = b""
        for sample in fsb.samples:
            rebuilt = fsb._rebuild_sample(sample)
            all_samples += rebuilt

        with open(output_path, "wb") as out_f:
            out_f.write(all_samples)

        print(f"[任务 {rank}] 存储于: {output_path}")

    except Exception as e:
        print(f"[任务 {rank}] 解析 {fsb_file} 产生错误: {e}")

# 同步所有进程完成
comm.barrier()

if rank == 0:
    print("所有并行作业已完成")