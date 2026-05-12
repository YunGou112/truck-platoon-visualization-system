from .visualizer_render import VEHICLE_MARKER_RADIUS


class PositionCalculator:
    """位置计算模块：计算标签的最终放置位置"""
    
    def __init__(self, config, collision_detector):
        """初始化位置计算器
        
        Args:
            config: 配置对象，包含位置计算相关的配置参数
            collision_detector: 碰撞检测器实例
        """
        self.config = config
        self.collision_detector = collision_detector
    
    def calculate_position(self, vehicle_x, vehicle_y, label_width, label_height, existing_rects, screen_width, screen_height):
        """计算标签的最终放置位置
        
        Args:
            vehicle_x: 车辆标记中心 x
            vehicle_y: 车辆标记中心 y
            label_width: 标签宽度
            label_height: 标签高度
            existing_rects: 已放置标签的碰撞体积矩形列表
            screen_width: 屏幕宽度
            screen_height: 屏幕高度
            
        Returns:
            dict: 标签的最终位置，包含x, y坐标和是否使用兜底方案
        """
        # 生成候选位置
        candidate_positions = self._generate_candidate_positions(vehicle_x, vehicle_y, label_width, label_height)
        
        # 车辆屏幕标记（圆点）碰撞区域，与 visualizer_render 一致
        mr = VEHICLE_MARKER_RADIUS
        truck_rect = {
            'x': vehicle_x - mr,
            'y': vehicle_y - mr,
            'width': mr * 2,
            'height': mr * 2,
        }
        
        # 按优先级检查候选位置
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
                
                # 检查是否与卡车本体碰撞
                if not self.collision_detector.check_collision(candidate_rect, existing_rects) and not self._is_colliding_with_truck(candidate_rect, truck_rect):
                    return {
                        'x': pos['x'],
                        'y': pos['y'],
                        'use_fallback': False
                    }
        
        # 所有候选位置都碰撞，使用兜底方案
        fallback_pos = self._calculate_fallback_position(vehicle_x, vehicle_y, label_width, label_height, existing_rects, screen_width, screen_height, truck_rect)
        return {
            'x': fallback_pos['x'],
            'y': fallback_pos['y'],
            'use_fallback': True
        }
    
    def _is_colliding_with_truck(self, candidate_rect, truck_rect):
        """检查候选位置是否与卡车本体碰撞
        
        Args:
            candidate_rect: 候选标签的碰撞体积矩形
            truck_rect: 卡车本体的碰撞体积矩形
            
        Returns:
            bool: True表示碰撞，False表示不碰撞
        """
        # 快速边界检查
        candidate_left = candidate_rect['x']
        candidate_right = candidate_rect['x'] + candidate_rect['width']
        candidate_top = candidate_rect['y']
        candidate_bottom = candidate_rect['y'] + candidate_rect['height']
        
        truck_left = truck_rect['x']
        truck_right = truck_rect['x'] + truck_rect['width']
        truck_top = truck_rect['y']
        truck_bottom = truck_rect['y'] + truck_rect['height']
        
        # 检查是否碰撞
        return not (
            candidate_right < truck_left or
            candidate_left > truck_right or
            candidate_bottom < truck_top or
            candidate_top > truck_bottom
        )
    
    def _generate_candidate_positions(self, vehicle_x, vehicle_y, label_width, label_height):
        """生成候选位置
        
        Args:
            vehicle_x: 车辆标记中心 x
            vehicle_y: 车辆标记中心 y
            label_width: 标签宽度
            label_height: 标签高度
            
        Returns:
            list: 候选位置列表，按优先级排序
        """
        # 候选位置优先级：右上 → 右下 → 左上 → 左下 → 正上 → 正下 → 正左 → 正右
        positions = []
        
        # 右上
        positions.append({
            'x': vehicle_x + 12,  # 与车辆标记间距 12 像素
            'y': vehicle_y - label_height - 12
        })
        
        # 右下
        positions.append({
            'x': vehicle_x + 12,
            'y': vehicle_y + 12
        })
        
        # 左上
        positions.append({
            'x': vehicle_x - label_width - 12,
            'y': vehicle_y - label_height - 12
        })
        
        # 左下
        positions.append({
            'x': vehicle_x - label_width - 12,
            'y': vehicle_y + 12
        })
        
        # 正上
        positions.append({
            'x': vehicle_x - label_width // 2,
            'y': vehicle_y - label_height - 12
        })
        
        # 正下
        positions.append({
            'x': vehicle_x - label_width // 2,
            'y': vehicle_y + 12
        })
        
        # 正左
        positions.append({
            'x': vehicle_x - label_width - 12,
            'y': vehicle_y - label_height // 2
        })
        
        # 正右
        positions.append({
            'x': vehicle_x + 12,
            'y': vehicle_y - label_height // 2
        })
        
        return positions
    
    def _is_in_screen(self, x, y, width, height, screen_width, screen_height):
        """检查位置是否在屏幕内
        
        Args:
            x: 位置x坐标
            y: 位置y坐标
            width: 标签宽度
            height: 标签高度
            screen_width: 屏幕宽度
            screen_height: 屏幕高度
            
        Returns:
            bool: True表示在屏幕内，False表示在屏幕外
        """
        return 0 <= x <= screen_width - width and 0 <= y <= screen_height - height
    
    def _calculate_fallback_position(self, vehicle_x, vehicle_y, label_width, label_height, existing_rects, screen_width, screen_height, truck_rect=None):
        """计算兜底位置（引线延伸）
        
        Args:
            vehicle_x: 车辆标记中心 x
            vehicle_y: 车辆标记中心 y
            label_width: 标签宽度
            label_height: 标签高度
            existing_rects: 已放置标签的碰撞体积矩形列表
            screen_width: 屏幕宽度
            screen_height: 屏幕高度
            truck_rect: 卡车本体的碰撞体积矩形
            
        Returns:
            dict: 兜底位置的x, y坐标
        """
        # 智能空白区域选择：优先选择车辆周围的最近空白区域
        
        # 搜索半径（从近到远）
        search_radius = [50, 100, 150, 200, 250]
        
        # 搜索方向（围绕车辆）
        directions = [
            {'dx': 1, 'dy': 0},   # 右侧
            {'dx': -1, 'dy': 0},  # 左侧
            {'dx': 0, 'dy': -1},  # 上方
            {'dx': 0, 'dy': 1},   # 下方
            {'dx': 1, 'dy': -1},  # 右上
            {'dx': 1, 'dy': 1},   # 右下
            {'dx': -1, 'dy': -1}, # 左上
            {'dx': -1, 'dy': 1}   # 左下
        ]
        
        # 从近到远搜索空白区域
        for radius in search_radius:
            for direction in directions:
                # 计算候选位置
                candidate_x = vehicle_x + direction['dx'] * radius
                candidate_y = vehicle_y + direction['dy'] * radius
                
                # 确保位置在屏幕内
                if 0 <= candidate_x <= screen_width - label_width and 0 <= candidate_y <= screen_height - label_height:
                    candidate_rect = {
                        'x': candidate_x,
                        'y': candidate_y,
                        'width': label_width,
                        'height': label_height
                    }
                    
                    # 检查是否与现有标签碰撞
                    collision = self.collision_detector.check_collision(candidate_rect, existing_rects)
                    
                    # 检查是否与卡车本体碰撞
                    if truck_rect:
                        collision = collision or self._is_colliding_with_truck(candidate_rect, truck_rect)
                    
                    if not collision:
                        return {'x': candidate_x, 'y': candidate_y}
        
        # 如果所有周围区域都有碰撞，再尝试屏幕边缘
        edge_positions = [
            {'x': 10, 'y': vehicle_y - label_height // 2},  # 左侧边缘
            {'x': screen_width - label_width - 10, 'y': vehicle_y - label_height // 2},  # 右侧边缘
            {'x': vehicle_x - label_width // 2, 'y': 10},  # 上边缘
            {'x': vehicle_x - label_width // 2, 'y': screen_height - label_height - 10}  # 下边缘
        ]
        
        for pos in edge_positions:
            # 确保位置在屏幕内
            if 0 <= pos['x'] <= screen_width - label_width and 0 <= pos['y'] <= screen_height - label_height:
                candidate_rect = {
                    'x': pos['x'],
                    'y': pos['y'],
                    'width': label_width,
                    'height': label_height
                }
                
                # 检查是否与现有标签碰撞
                collision = self.collision_detector.check_collision(candidate_rect, existing_rects)
                
                # 检查是否与卡车本体碰撞
                if truck_rect:
                    collision = collision or self._is_colliding_with_truck(candidate_rect, truck_rect)
                
                if not collision:
                    return pos
        
        # 如果所有位置都有碰撞，返回车辆右侧的位置
        return {
            'x': max(0, min(screen_width - label_width, vehicle_x + 200)),
            'y': max(0, min(screen_height - label_height, vehicle_y - label_height // 2))
        }