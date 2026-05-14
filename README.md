# Truck Platoon Visualization System

面向卡车编队历史轨迹数据的本地可视化分析工程。项目包含数据预处理脚本、PyQt 启动器和 Pygame 可视化主程序，适合做编队运行回放、车辆状态观察、预警事件分析和结果导出。

## 1. 项目定位

这个仓库当前提供三类能力：

1. 数据处理  
   将原始车辆轨迹数据拆分、识别和整理为编队结果目录。
2. 可视化回放  
   以时间轴方式回放单个编队或多个编队目录中的历史数据。
3. 交互式分析  
   在界面内查看车辆状态、预警事件、关键指标，并导出当前结果。

## 2. 主要功能

- 支持从 `platoon_results/<编队目录>/platoon_data.csv` 读取数据
- 支持自动识别车辆 ID 字段
- 支持自动兼容多种经纬度字段命名
- 支持 PyQt 启动器选择数据目录并启动可视化
- 支持 Pygame 主界面播放、暂停、变速、拖动时间轴
- 支持地图缩放、平移、自动聚焦编队主体
- 支持车辆轨迹、速度、加速度、车头时距等信息显示
- 支持选中车辆后的全界面联动
- 支持预警列表滚动、点击、排序、分类、筛选
- 支持跳转到上一条/下一条预警
- 支持导出当前数据和异常事件

## 3. 运行环境

建议环境：

- Python 3.9 及以上
- Windows 10 / 11

安装依赖：

```bash
pip install -r requirements.txt
```

## 4. 依赖说明

当前工程代码实际依赖如下：

- `pygame`：主可视化渲染与交互
- `pandas`：CSV 读取、时间解析、数据整理
- `PyQt5`：启动器与启动提示窗口
- `matplotlib`：工具脚本中的绘图支持

## 5. 数据格式要求

可视化程序默认读取目标目录下的 `platoon_data.csv`。

至少需要以下字段：

- `timestamp_str`
- 车辆 ID 字段之一：
  - `vehicle_id`
  - `truck_id`
  - `id`
  - `vehicleId`
  - `ID`
- 坐标字段之一：
  - `lon` + `lat`
  - `lon_wgs84` + `lat_wgs84`
  - `lon_gcj02` + `lat_gcj02`
  - `lon_bd09` + `lat_bd09`

建议额外包含：

- `speed`
- 可用于状态分析的其他业务字段

## 6. 启动方式

### 方式 A：启动器

```bash
python truck_platoon_viz/run_launcher.py
```

适用场景：

- 需要图形化选择数据目录
- 需要更稳定的启动路径
- 需要统一的项目入口

### 方式 B：命令行直接启动

```bash
python truck_platoon_viz/main.py "platoon_results/9mins_4trucks"
```

如果不传参数，程序会尝试从 `platoon_results/` 中选择一个默认目录启动。

## 7. 常用交互

- `Space`：播放 / 暂停
- `Up / Down / Left / Right / + / -`：调整播放速度
- `R`：重置播放状态
- 鼠标滚轮：缩放或滚动预警列表
- 鼠标左键拖动：平移主视图
- 点击车辆：选中车辆并联动侧边信息
- 点击预警：跳转到对应事件时间点

## 8. 预警与分析

当前预警规则定义在 `config.py` 中，核心阈值包括：

- 最小安全距离：`20 m`
- 最大绝对加速度：`3.0 m/s²`
- 最大速度：`90 km/h`
- 去抖帧数：`2`

当前界面支持：

- 最新预警提示
- 预警事件列表
- 预警按时间排序
- 预警按车辆分类
- 预警按类型分类
- 上一条 / 下一条预警跳转

## 9. 数据处理脚本

统一入口：

```bash
python tools/data_pipeline.py [split|analyze|metrics|all]
```

含义如下：

- `split`：执行原始数据拆分
- `analyze`：执行编队识别分析
- `metrics`：计算编队结果指标
- `all`：顺序执行全部流程

## 10. 测试与自检

冒烟测试：

```bash
python tools/smoke_test.py
```

单元测试：

```bash
python -m unittest tests.test_data_processor -v
```

## 11. 目录结构

```text
.
├─ assets/                    运行时图片资源
├─ platoon_results/           编队样例与分析结果数据
├─ tests/                     自动化测试
├─ tools/                     数据处理与辅助脚本
├─ truck_platoon_viz/         主程序、渲染逻辑、启动器
├─ config.py                  全局配置与预警阈值
├─ requirements.txt           Python 依赖
└─ README.md                  项目说明
```

## 12. 当前工程边界

这个项目目前更偏“研究演示型分析工具”，不是通用商用产品，主要边界有：

- 默认以本地 CSV 数据为输入，没有在线数据源接入
- 预警规则是固定阈值逻辑，不是可配置规则引擎
- 工具脚本与主程序共用一个仓库，但还没有做成完整安装包
- 文本、字体和中文显示效果会受本机字体环境影响

## 13. 推荐提交与部署范围

如果只是把项目交给另一台电脑运行，至少保留这些内容：

- `truck_platoon_viz/`
- `platoon_results/` 中至少一个可用数据目录
- `assets/`
- `config.py`
- `requirements.txt`

然后执行：

```bash
pip install -r requirements.txt
python truck_platoon_viz/run_launcher.py
```
