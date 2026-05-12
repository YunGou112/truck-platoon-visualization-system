import matplotlib.pyplot as plt
import matplotlib

# 设置中文字体（Windows系统）
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']  # 用来正常显示中文标签
matplotlib.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 车辆数量
vehicle_counts = [2, 4, 6]

# 对应FPS（请替换为你的实测数据）
fps_values = [58.7, 56.3, 54.9]

plt.figure(figsize=(8, 5), dpi=150)

# 柱状图
bars = plt.bar(vehicle_counts, fps_values, width=0.9, alpha=0.75, label='FPS (bar)')

# 折线图
plt.plot(vehicle_counts, fps_values, color='red', marker='o', linewidth=2, label='FPS (line)')

# 数值标注
for x, y in zip(vehicle_counts, fps_values):
    plt.text(x, y + 0.6, f"{y:.1f}", ha='center', va='bottom', fontsize=10)

plt.title('不同车辆数量下系统帧率（FPS）')
plt.xlabel('车辆数量（辆）')
plt.ylabel('帧率 FPS')
plt.xticks(vehicle_counts, [str(v) for v in vehicle_counts])
plt.grid(axis='y', linestyle='--', alpha=0.35)
plt.legend()
plt.tight_layout()

# 保存图片（可直接插论文）
plt.savefig('fps_compare_2_4_6.png', bbox_inches='tight')
plt.show()