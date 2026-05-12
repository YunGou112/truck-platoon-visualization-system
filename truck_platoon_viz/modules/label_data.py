class LabelDataGenerator:
    """标签数据生成模块：生成单辆车的标准化标签数据"""
    
    def __init__(self, config):
        """初始化标签数据生成器
        
        Args:
            config: 配置对象，包含标签相关的配置参数
        """
        self.config = config
    
    def generate_label_data(self, truck):
        """生成单辆车的标签数据
        
        Args:
            truck: 卡车对象，包含ID、速度、加速度等信息
            
        Returns:
            dict: 标准化的标签数据，包含文本、尺寸、碰撞体积等信息
        """
        # 获取车辆参数
        truck_id = truck.id
        speed = truck.get_speed()
        acceleration = truck.get_acceleration()
        
        # 生成标签文本
        label_text = f"{truck_id}\n速度: {speed:.1f} km/h\n加速度: {acceleration:.2f} m/s²"
        
        # 计算标签尺寸
        label_width = self.config.get('label_width', 120)
        label_height = self.config.get('label_height', 60)
        
        # 生成碰撞体积（默认与标签尺寸一致）
        collision_rect = {
            'width': label_width,
            'height': label_height
        }
        
        return {
            'text': label_text,
            'width': label_width,
            'height': label_height,
            'collision_rect': collision_rect,
            'truck_id': truck_id,
            'speed': speed,
            'acceleration': acceleration
        }