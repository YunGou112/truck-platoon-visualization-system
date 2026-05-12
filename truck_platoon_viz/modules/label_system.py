import json
from .label_data import LabelDataGenerator
from .collision import CollisionDetector
from .position import PositionCalculator
from .label_renderer import LabelRenderer
from .distance_label import DistanceLabelSystem

class LabelSystem:
    """标签系统：整合所有标签相关模块"""
    
    def __init__(self, config_path=None):
        """初始化标签系统
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        if config_path:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                self.config = {
                    'label_width': config_data.get('label', {}).get('width', 120),
                    'label_height': config_data.get('label', {}).get('height', 60),
                    'label_padding': config_data.get('label', {}).get('padding', 10),
                    'label_background_color': tuple(config_data.get('label', {}).get('background_color', [0, 0, 0, 217])),
                    'label_border_radius': config_data.get('label', {}).get('border_radius', 3),
                    'leader_line_width': config_data.get('leader_line', {}).get('width', 2),
                    'leader_line_color': tuple(config_data.get('leader_line', {}).get('color', [255, 255, 255, 128])),
                    'candidate_priorities': config_data.get('position', {}).get('candidate_priorities', ['top_right', 'bottom_right', 'top_left', 'bottom_left', 'top', 'bottom', 'left', 'right'])
                }
        else:
            # 默认配置
            self.config = {
                'label_width': 120,
                'label_height': 60,
                'label_padding': 10,
                'label_background_color': (0, 0, 0, 217),
                'label_border_radius': 3,
                'leader_line_width': 2,
                'leader_line_color': (255, 255, 255, 128),
                'candidate_priorities': ['top_right', 'bottom_right', 'top_left', 'bottom_left', 'top', 'bottom', 'left', 'right']
            }
        
        # 初始化各个模块
        self.label_data_generator = LabelDataGenerator(self.config)
        self.collision_detector = CollisionDetector(self.config)
        self.position_calculator = PositionCalculator(self.config, self.collision_detector)
        self.label_renderer = LabelRenderer(self.config)
        self.distance_label_system = DistanceLabelSystem(self.config, self.collision_detector)
    
    def process_labels(self, screen, trucks, screen_width, screen_height):
        """处理所有卡车的标签
        
        Args:
            screen: Pygame屏幕对象
            trucks: 卡车对象列表
            screen_width: 屏幕宽度
            screen_height: 屏幕高度
        """
        # 按队列顺序排序（假设按x坐标排序，模拟头车到尾车）
        sorted_trucks = sorted(trucks, key=lambda t: t.current_pos_data['lon'] if t.current_pos_data else 0, reverse=True)
        
        # 存储已放置标签的碰撞体积
        existing_rects = []
        
        # 处理每辆卡车的标签
        for truck in sorted_trucks:
            if truck.current_pos_data:
                # 生成标签数据
                label_data = self.label_data_generator.generate_label_data(truck)
                
                # 计算车辆标记中心（圆点）
                vehicle_x = truck.current_pos_data.get('screen_x', 0)
                vehicle_y = truck.current_pos_data.get('screen_y', 0)
                
                # 计算标签位置
                position = self.position_calculator.calculate_position(
                    vehicle_x, vehicle_y, 
                    label_data['width'], label_data['height'], 
                    existing_rects, 
                    screen_width, screen_height
                )
                
                # 渲染标签
                # 获取车辆颜色（假设truck对象有color属性）
                vehicle_color = getattr(truck, 'color', None)
                if not vehicle_color:
                    # 如果truck对象没有color属性，使用默认颜色
                    vehicle_color = (0, 128, 255)  # 默认蓝色
                
                self.label_renderer.render_label(
                    screen, label_data, position, vehicle_x, vehicle_y, vehicle_color, trucks, existing_rects
                )
                
                # 添加到已放置标签列表
                existing_rects.append({
                    'x': position['x'],
                    'y': position['y'],
                    'width': label_data['width'],
                    'height': label_data['height']
                })
        
        # 处理车距标注
        self.distance_label_system.process_distance_labels(screen, sorted_trucks, existing_rects, screen_width, screen_height)