import pygame

from .visualizer_render import VEHICLE_MARKER_RADIUS


class LabelRenderer:
    """标签渲染模块：渲染标签到界面"""
    
    def __init__(self, config):
        """初始化标签渲染器
        
        Args:
            config: 配置对象，包含渲染相关的配置参数
        """
        self.config = config
        
        # 初始化字体
        try:
            self.font = pygame.font.SysFont("Microsoft YaHei", 12)
            self.bold_font = pygame.font.SysFont("Microsoft YaHei", 12, bold=True)
        except:
            self.font = pygame.font.Font(None, 12)
            self.bold_font = pygame.font.Font(None, 12)
    
    def render_label(self, screen, label_data, position, vehicle_x, vehicle_y, vehicle_color=None, trucks=None, existing_rects=None):
        """渲染标签到界面
        
        Args:
            screen: Pygame屏幕对象
            label_data: 标签数据，包含文本、尺寸等信息
            position: 标签位置，包含x, y坐标和是否使用兜底方案
            vehicle_x: 车辆图标的x坐标
            vehicle_y: 车辆图标的y坐标
            vehicle_color: 车辆颜色，用于引线颜色
            trucks: 卡车对象列表，用于碰撞检测
            existing_rects: 已放置标签的碰撞体积矩形列表，用于碰撞检测
        """
        # 绘制引线（如果使用兜底方案）
        if position['use_fallback']:
            self._draw_leader_line(screen, vehicle_x, vehicle_y, position['x'] + label_data['width'] // 2, position['y'] + label_data['height'] // 2, vehicle_color, trucks, existing_rects)
        
        # 绘制标签背景
        self._draw_label_background(screen, position['x'], position['y'], label_data['width'], label_data['height'])
        
        # 绘制标签文本
        self._draw_label_text(screen, label_data, position['x'], position['y'])
    
    def _draw_leader_line(self, screen, start_x, start_y, end_x, end_y, vehicle_color=None, trucks=None, existing_rects=None):
        """绘制引线
        
        Args:
            screen: Pygame屏幕对象
            start_x: 起点x坐标
            start_y: 起点y坐标
            end_x: 终点x坐标
            end_y: 终点y坐标
            vehicle_color: 车辆颜色，用于引线颜色
            trucks: 卡车对象列表，用于碰撞检测
            existing_rects: 已放置标签的碰撞体积矩形列表，用于碰撞检测
        """
        # 获取引线样式配置
        line_width = self.config.get('leader_line_width', 2)
        
        # 使用车辆颜色作为引线颜色，如果没有则使用默认颜色
        if vehicle_color:
            # 创建半透明版本的车辆颜色
            line_color = (vehicle_color[0], vehicle_color[1], vehicle_color[2], 128)  # 80%透明度
        else:
            line_color = self.config.get('leader_line_color', (255, 255, 255, 128))  # 半透明白色
        
        # 检查引线是否需要绕开障碍物
        points = self._calculate_leader_line_path(start_x, start_y, end_x, end_y, trucks, existing_rects)
        
        # 绘制引线
        if len(points) >= 2:
            for i in range(len(points) - 1):
                pygame.draw.line(screen, line_color, points[i], points[i+1], line_width)
        else:
            pygame.draw.line(screen, line_color, (start_x, start_y), (end_x, end_y), line_width)
    
    def _calculate_leader_line_path(self, start_x, start_y, end_x, end_y, trucks=None, existing_rects=None):
        """计算引线路径，避开障碍物
        
        Args:
            start_x: 起点x坐标
            start_y: 起点y坐标
            end_x: 终点x坐标
            end_y: 终点y坐标
            trucks: 卡车对象列表，用于碰撞检测
            existing_rects: 已放置标签的碰撞体积矩形列表，用于碰撞检测
            
        Returns:
            list: 路径点列表
        """
        # 生成初始直线路径
        points = [(start_x, start_y), (end_x, end_y)]
        
        # 检查是否有障碍物
        if trucks or existing_rects:
            # 检查是否与卡车碰撞
            if trucks:
                for truck in trucks:
                    if hasattr(truck, 'current_pos_data') and truck.current_pos_data:
                        truck_x = truck.current_pos_data.get('screen_x', 0)
                        truck_y = truck.current_pos_data.get('screen_y', 0)
                        mr = VEHICLE_MARKER_RADIUS
                        truck_rect = {
                            'x': truck_x - mr,
                            'y': truck_y - mr,
                            'width': mr * 2,
                            'height': mr * 2,
                        }
                        # 检查引线是否与卡车碰撞
                        if self._line_intersects_rect((start_x, start_y), (end_x, end_y), truck_rect):
                            # 计算绕开路径
                            points = self._calculate_detour_path(start_x, start_y, end_x, end_y, truck_rect)
                            break
            
            # 检查是否与标签碰撞
            if existing_rects:
                for rect in existing_rects:
                    # 检查引线是否与标签碰撞
                    if self._line_intersects_rect((start_x, start_y), (end_x, end_y), rect):
                        # 计算绕开路径
                        points = self._calculate_detour_path(start_x, start_y, end_x, end_y, rect)
                        break
        
        return points
    
    def _line_intersects_rect(self, p1, p2, rect):
        """检查线段是否与矩形碰撞
        
        Args:
            p1: 线段起点
            p2: 线段终点
            rect: 矩形
            
        Returns:
            bool: True表示碰撞，False表示不碰撞
        """
        # 矩形边界
        rect_left = rect['x']
        rect_right = rect['x'] + rect['width']
        rect_top = rect['y']
        rect_bottom = rect['y'] + rect['height']
        
        # 线段端点
        x1, y1 = p1
        x2, y2 = p2
        
        # 检查线段是否与矩形边界相交
        # 左边界
        if self._line_intersects_line(p1, p2, (rect_left, rect_top), (rect_left, rect_bottom)):
            return True
        # 右边界
        if self._line_intersects_line(p1, p2, (rect_right, rect_top), (rect_right, rect_bottom)):
            return True
        # 上边界
        if self._line_intersects_line(p1, p2, (rect_left, rect_top), (rect_right, rect_top)):
            return True
        # 下边界
        if self._line_intersects_line(p1, p2, (rect_left, rect_bottom), (rect_right, rect_bottom)):
            return True
        # 检查线段是否完全在矩形内部
        if rect_left <= x1 <= rect_right and rect_top <= y1 <= rect_bottom:
            return True
        if rect_left <= x2 <= rect_right and rect_top <= y2 <= rect_bottom:
            return True
        
        return False
    
    def _line_intersects_line(self, p1, p2, p3, p4):
        """检查两条线段是否相交
        
        Args:
            p1: 第一条线段的起点
            p2: 第一条线段的终点
            p3: 第二条线段的起点
            p4: 第二条线段的终点
            
        Returns:
            bool: True表示相交，False表示不相交
        """
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        
        # 计算分母
        denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
        if denom == 0:
            return False
        
        # 计算参数
        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom
        
        # 检查交点是否在线段上
        if 0 <= ua <= 1 and 0 <= ub <= 1:
            return True
        
        return False
    
    def _calculate_detour_path(self, start_x, start_y, end_x, end_y, obstacle_rect):
        """计算绕开障碍物的路径
        
        Args:
            start_x: 起点x坐标
            start_y: 起点y坐标
            end_x: 终点x坐标
            end_y: 终点y坐标
            obstacle_rect: 障碍物矩形
            
        Returns:
            list: 路径点列表
        """
        # 计算障碍物的中心
        obstacle_center_x = obstacle_rect['x'] + obstacle_rect['width'] // 2
        obstacle_center_y = obstacle_rect['y'] + obstacle_rect['height'] // 2
        
        # 计算起点到障碍物中心的向量
        dx = obstacle_center_x - start_x
        dy = obstacle_center_y - start_y
        
        # 计算垂直方向的偏移量（绕开障碍物）
        offset_distance = max(obstacle_rect['width'], obstacle_rect['height']) // 2 + 20
        
        # 计算绕开点
        if abs(dx) > abs(dy):
            # 水平方向偏移
            detour_x = obstacle_center_x + offset_distance * (1 if dx > 0 else -1)
            detour_y = obstacle_center_y
        else:
            # 垂直方向偏移
            detour_x = obstacle_center_x
            detour_y = obstacle_center_y + offset_distance * (1 if dy > 0 else -1)
        
        # 生成绕开路径
        return [(start_x, start_y), (detour_x, detour_y), (end_x, end_y)]
    
    def _draw_label_background(self, screen, x, y, width, height):
        """绘制标签背景
        
        Args:
            screen: Pygame屏幕对象
            x: 标签x坐标
            y: 标签y坐标
            width: 标签宽度
            height: 标签高度
        """
        # 获取背景样式配置
        background_color = self.config.get('label_background_color', (0, 0, 0, 217))  # 半透黑色（透明度85%）
        border_radius = self.config.get('label_border_radius', 3)
        
        # 绘制背景
        pygame.draw.rect(screen, background_color, (x, y, width, height), border_radius=border_radius)
    
    def _draw_label_text(self, screen, label_data, x, y):
        """绘制标签文本
        
        Args:
            screen: Pygame屏幕对象
            label_data: 标签数据，包含文本、尺寸等信息
            x: 标签x坐标
            y: 标签y坐标
        """
        # 解析标签文本
        lines = label_data['text'].split('\n')
        
        # 绘制文本
        line_height = 20  # 行高
        for i, line in enumerate(lines):
            if i == 0:  # 第一行是车辆ID，使用粗体
                text_surface = self.bold_font.render(line, True, (255, 255, 255))
            else:  # 其他行使用普通字体
                text_surface = self.font.render(line, True, (255, 255, 255))
            
            # 绘制文本（左对齐）
            screen.blit(text_surface, (x + 10, y + 10 + i * line_height))