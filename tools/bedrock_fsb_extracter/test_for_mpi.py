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
    print("载入 sound_definitions.json 定义文件", flush=True)

    # 加载 JSON 配置
    with open("sounds/sound_definitions.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    sound_definitions = data.get("sound_definitions", {})

    # 构建任务列表：(sound_name, full_path)
    tasks = []
    for sound_name, entry in sound_definitions.items():
        sounds_list = entry.get("sounds", [])
        if not sounds_list:
            continue

        for item in sorted(
            sounds_list,
            key=(lambda x: x.get("weight", 1) if isinstance(x, dict) else 1),
            reverse=True,
        ):
            if isinstance(item, dict):
                file_path = item.get("name", "")
            else:
                file_path = item
            if not file_path:
                continue
            full_path = os.path.join(file_path + ".fsb")
            tasks.append((sound_name, full_path))
            break

    # 分发任务给各个进程
    print(f"[任务 {rank}] 文件解析完成，共需分配 {len(tasks)} 个任务", flush=True)

    chunks = [tasks[i::size] for i in range(size)]
else:
    chunks = None

# 各进程接收自己的任务
local_tasks = comm.scatter(chunks, root=0)
total_count = len(local_tasks)

print(f"[任务 {rank}] 正在解析 {total_count} 个文件...", flush=True)

# 处理本机任务
for _i, tkk in enumerate(local_tasks):
    sound_name, fsb_file = tkk

    print(f"[任务 {rank}] \t正在处理[{_i}/{total_count}]: {sound_name}", flush=True)

    if not os.path.isfile(fsb_file):
        print(f"[任务 {rank}] \t无法找到文件: {fsb_file}", flush=True)
        continue

    try:
        with open(fsb_file, "rb") as f:
            fsb_data = BytesIO(f.read())
            fsb = fsb5.FSB5(fsb_data)

        ext = fsb.get_sample_extension()
        output_path = os.path.join("output", f"{sound_name}.wav")

        # 避免同一个FSB中包含多个采样，此处合为一个文件
        # 在测试范围内不会出现此种情况
        all_samples = b""
        for sample in fsb.samples:
            rebuilt = fsb._rebuild_sample(sample)
            all_samples += rebuilt

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "wb") as out_f:
            out_f.write(all_samples)

        print(f"[任务 {rank}] \t存储于: {output_path}", flush=True)

    except Exception as e:
        print(f"[任务 {rank}] \t解析 {fsb_file} 产生错误: {e}", flush=True)
        continue

# 同步所有进程完成
comm.barrier()

if rank == 0:
    print("所有并行作业已完成", flush=True)
