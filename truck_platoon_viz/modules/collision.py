class CollisionDetector:
    """碰撞检测模块：检测标签位置是否与已放置标签碰撞"""
    
    def __init__(self, config):
        """初始化碰撞检测器
        
        Args:
            config: 配置对象，包含碰撞检测相关的配置参数
        """
        self.config = config
    
    def check_collision(self, candidate_rect, existing_rects):
        """检查候选位置是否与现有标签碰撞
        
        Args:
            candidate_rect: 候选标签的碰撞体积矩形，包含x, y, width, height
            existing_rects: 已放置标签的碰撞体积矩形列表
            
        Returns:
            bool: True表示存在碰撞，False表示无碰撞
        """
        # 获取避让间距
        padding = self.config.get('label_padding', 10)
        
        # 快速边界检查，减少计算量
        candidate_left = candidate_rect['x'] - padding
        candidate_right = candidate_rect['x'] + candidate_rect['width'] + padding
        candidate_top = candidate_rect['y'] - padding
        candidate_bottom = candidate_rect['y'] + candidate_rect['height'] + padding
        
        # 遍历现有标签的碰撞体积
        for rect in existing_rects:
            rect_left = rect['x'] - padding
            rect_right = rect['x'] + rect['width'] + padding
            rect_top = rect['y'] - padding
            rect_bottom = rect['y'] + rect['height'] + padding
            
            # 快速检查是否可能碰撞
            if not (candidate_right < rect_left or 
                    candidate_left > rect_right or 
                    candidate_bottom < rect_top or 
                    candidate_top > rect_bottom):
                return True
        
        return False
    
    def _is_colliding(self, rect1, rect2, padding):
        """检查两个矩形是否碰撞
        
        Args:
            rect1: 第一个矩形，包含x, y, width, height
            rect2: 第二个矩形，包含x, y, width, height
            padding: 避让间距
            
        Returns:
            bool: True表示碰撞，False表示不碰撞
        """
        # 扩展矩形以包含避让间距
        rect1_left = rect1['x'] - padding
        rect1_right = rect1['x'] + rect1['width'] + padding
        rect1_top = rect1['y'] - padding
        rect1_bottom = rect1['y'] + rect1['height'] + padding
        
        rect2_left = rect2['x'] - padding
        rect2_right = rect2['x'] + rect2['width'] + padding
        rect2_top = rect2['y'] - padding
        rect2_bottom = rect2['y'] + rect2['height'] + padding
        
        # 检查是否碰撞
        return not (
            rect1_right < rect2_left or
            rect1_left > rect2_right or
            rect1_bottom < rect2_top or
            rect1_top > rect2_bottom
        )