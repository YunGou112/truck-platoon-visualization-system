import pygame

class DistanceLabelSystem:
    """车距标注系统：负责处理车距标签的生成、位置计算和渲染"""
    
    def __init__(self, config, collision_detector):
        """初始化车距标注系统
        
        Args:
            config: 配置对象，包含车距标注相关的配置参数
            collision_detector: 碰撞检测器实例
        """
        self.config = config
        self.collision_detector = collision_detector
        
        # 初始化字体
        try:
            self.font = pygame.font.SysFont("Microsoft YaHei", 11)
        except Exception:
            self.font = pygame.font.Font(None, 11)
    
    def process_distance_labels(self, screen, trucks, existing_rects, screen_width, screen_height):
        """处理所有车距标注
        
        Args:
            screen: Pygame屏幕对象
            trucks: 卡车对象列表
            existing_rects: 已放置标签的碰撞体积矩形列表
            screen_width: 屏幕宽度
            screen_height: 屏幕高度
        """
        # 按队列顺序排序（假设按x坐标排序，模拟头车到尾车）
        sorted_trucks = sorted(trucks, key=lambda t: t.current_pos_data['lon'] if t.current_pos_data else 0, reverse=True)
        
        # 处理每对相邻卡车的车距标注
        for i in range(len(sorted_trucks) - 1):
            truck1 = sorted_trucks[i]
            truck2 = sorted_trucks[i + 1]
            
            if truck1.current_pos_data and truck2.current_pos_data:
                # 计算车距
                headway_dist = truck1.get_headway_distance(truck2)
                if headway_dist < 1000:  # 只显示1公里内的车辆
                    # 计算两车中间位置
                    x1, y1 = truck1.current_pos_data.get('screen_x', 0), truck1.current_pos_data.get('screen_y', 0)
                    x2, y2 = truck2.current_pos_data.get('screen_x', 0), truck2.current_pos_data.get('screen_y', 0)
                    mid_x = (x1 + x2) // 2
                    mid_y = (y1 + y2) // 2
                    
                    # 生成车距标签数据
                    label_data = self._generate_label_data(headway_dist)
                    
                    # 计算标签位置
                    position = self._calculate_position(mid_x, mid_y, label_data['width'], label_data['height'], existing_rects, screen_width, screen_height)
                    
                    # 渲染标签
                    if position:
                        self._render_label(screen, label_data, position)
                        
                        # 添加到已放置标签列表
                        existing_rects.append({
                            'x': position['x'],
                            'y': position['y'],
                            'width': label_data['width'],
                            'height': label_data['height']
                        })
    
    def _generate_label_data(self, distance):
        """生成车距标签数据
        
        Args:
            distance: 车距值
            
        Returns:
            dict: 车距标签数据
        """
        # 生成标签文本
        label_text = f"{distance:.1f}m"
        
        # 统一车距标签尺寸为80×30px
        label_width = 80
        label_height = 30
        
        return {
            'text': label_text,
            'width': label_width,
            'height': label_height
        }
    
    def _calculate_position(self, mid_x, mid_y, label_width, label_height, existing_rects, screen_width, screen_height):
        """计算车距标签的位置
        
        Args:
            mid_x: 两车中间点x坐标
            mid_y: 两车中间点y坐标
            label_width: 标签宽度
            label_height: 标签高度
            existing_rects: 已放置标签的碰撞体积矩形列表
            screen_width: 屏幕宽度
            screen_height: 屏幕高度
            
        Returns:
            dict: 标签位置，包含x, y坐标
        """
        # 尝试多个候选位置，避免与其他标签重叠
        candidate_positions = [
            {'x': mid_x - label_width // 2, 'y': mid_y - label_height - 10},  # 上方
            {'x': mid_x - label_width // 2, 'y': mid_y + 10},  # 下方
            {'x': mid_x - label_width - 10, 'y': mid_y - label_height // 2},  # 左侧
            {'x': mid_x + 10, 'y': mid_y - label_height // 2},  # 右侧
            {'x': mid_x - label_width // 2, 'y': mid_y - label_height // 2}  # 中间
        ]
        
        # 检查每个候选位置
        for pos in candidate_positions:
            # 检查位置是否在屏幕内
            if 0 <= pos['x'] <= screen_width - label_width and 0 <= pos['y'] <= screen_height - label_height:
                # 检查是否与现有标签碰撞
                candidate_rect = {
                    'x': pos['x'],
                    'y': pos['y'],
                    'width': label_width,
                    'height': label_height
                }
                
                if not self.collision_detector.check_collision(candidate_rect, existing_rects):
                    return pos
        
        # 如果所有位置都有碰撞，返回一个默认位置
        return None
    
    def _render_label(self, screen, label_data, position):
        """渲染车距标签
        
        Args:
            screen: Pygame屏幕对象
            label_data: 车距标签数据
            position: 标签位置
        """
        # 绘制半透黑色背景
        background_color = self.config.get('label_background_color', (0, 0, 0, 217))
        pygame.draw.rect(screen, background_color, (position['x'], position['y'], label_data['width'], label_data['height']), border_radius=3)
        
        # 绘制文字
        text_surface = self.font.render(label_data['text'], True, (255, 255, 255))
        text_x = position['x'] + (label_data['width'] - text_surface.get_width()) // 2
        text_y = position['y'] + (label_data['height'] - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))
