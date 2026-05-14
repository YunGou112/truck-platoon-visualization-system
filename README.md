# 卡车编队可视化系统

本项目用于对卡车编队历史轨迹数据进行回放与可视化分析，支持播放控制、轨迹显示、参数标签、异常预警显示。

## 1. 环境准备

建议使用 Python 3.10+（Windows）。

```bash
pip install -r requirements.txt
```

## 2. 数据要求

可视化程序读取 `platoon_data.csv`，至少需要以下字段：

- `timestamp_str`
- `vehicle_id`（或 `truck_id` / `id` / `vehicleId` / `ID`）
- 坐标列之一：
  - `lon` + `lat`
  - `lon_wgs84` + `lat_wgs84`
  - `lon_gcj02` + `lat_gcj02`
  - `lon_bd09` + `lat_bd09`
- `speed`

推荐直接使用项目内 `platoon_results/*/platoon_data.csv`。

## 3. 启动方式

### 方式 A：启动器（推荐）

```bash
python truck_platoon_viz/run_launcher.py
```

然后在启动器中选择数据文件夹（例如某个 `platoon_results/xxx` 目录），点击启动。

### 方式 B：命令行直启

```bash
python truck_platoon_viz/main.py "platoon_results/9mins_4trucks"
```

## 4. 主要交互

- `Space`：播放/暂停
- `Up/Down/Left/Right/+/-`：加速/减速
- `R`：重置
- `A/D`：切换编队
- 鼠标滚轮：缩放
- 鼠标左键拖动：平移

## 5. 预警规则（当前版本）

预警规则位于根目录 `config.py`：

- 最小安全车距：20 m
- 最大绝对加速度：3.0 m/s²
- 最大速度：90 km/h
- 去抖动：连续 2 帧触发才报警

状态面板会显示最新预警文本，车辆异常时显示红色。
按 `E` 导出当前数据时，会同时导出异常事件 CSV（如果有预警事件）。

## 6. 当前工程目录

- `truck_platoon_viz/`：可视化主程序
- `platoon_results/`：样例编队数据
- `tools/data/`：数据预处理与统计脚本
- `tools/data_pipeline.py`：统一数据处理入口
- `tools/plots/`：工程辅助绘图脚本
- `tools/smoke_test.py`：环境冒烟测试
- `tests/`：自动化测试
- `requirements.txt`：依赖清单
- `config.py`：全局阈值和参数

## 7. 在其他电脑运行，最少需要哪些文件

只做“运行可视化”时，保留下面这些即可：

- `requirements.txt`
- `config.py`
- `truck_platoon_viz/`（整个目录）
- `platoon_results/`（至少一个包含 `platoon_data.csv` 的子目录）

安装与运行：

```bash
pip install -r requirements.txt
python truck_platoon_viz/run_launcher.py
```

## 8. 工程说明

当前仓库只保留工程相关内容：

- 可视化主程序与启动器
- 数据预处理与指标计算脚本
- 工程测试与冒烟验证脚本
- 样例数据与运行资源

PPT、答辩排版、演示稿生成等非工程内容已从当前工程树中移除。
