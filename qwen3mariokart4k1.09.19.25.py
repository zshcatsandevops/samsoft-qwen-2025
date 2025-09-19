from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import basic_lighting_shader, lit_with_shadows_shader
import random
import math

app = Ursina()

# Game settings - N64 style (lower resolution for authentic feel)
window.borderless = False
window.fullscreen = False
window.title = 'Mario Kart 64 Clone'
window.exit_button.visible = False
window.size = (640, 480)  # N64-like resolution

# N64 style colors
n64_blue = color.rgb(60, 120, 216)
n64_red = color.rgb(216, 60, 60)
n64_green = color.rgb(60, 216, 120)
n64_yellow = color.rgb(255, 216, 60)
n64_purple = color.rgb(180, 60, 216)

# N64 style track generation
def generate_track():
    track_entities = []
    obstacles = []
    items = []
    
    # Create a more interesting track shape (like Mario Kart 64's Royal Raceway)
    segments = 36
    track_radius = 25
    for i in range(segments):
        angle = (i / segments) * 360
        x = math.cos(math.radians(angle)) * track_radius
        z = math.sin(math.radians(angle)) * track_radius
        
        # Vary the height for hills
        y = -0.5 + math.sin(math.radians(angle * 3)) * 2
        
        road = Entity(
            model='cube',
            color=n64_blue,
            position=(x, y, z),
            scale=(8, 0.1, 3),
            rotation=(0, angle, 0),
            texture='white_cube',
            texture_scale=(4, 1)
        )
        track_entities.append(road)
        
        # Add road borders
        border1 = Entity(
            model='cube',
            color=n64_red,
            position=(x + 4, y + 0.1, z),
            scale=(0.5, 0.3, 3),
            rotation=(0, angle, 0)
        )
        
        border2 = Entity(
            model='cube',
            color=n64_red,
            position=(x - 4, y + 0.1, z),
            scale=(0.5, 0.3, 3),
            rotation=(0, angle, 0)
        )
        
        track_entities.extend([border1, border2])
        
        # Add checkpoints every 6 segments
        if i % 6 == 0:
            checkpoint = Entity(
                model='cube',
                color=n64_yellow,
                position=(x, y + 0.2, z),
                scale=(8, 0.2, 0.2),
                rotation=(0, angle, 0),
                collider='box'
            )
            track_entities.append(checkpoint)
    
    # Add some obstacles and items in N64 style
    for i in range(15):
        angle = random.randint(0, 360)
        dist = random.uniform(15, 22)
        x = math.cos(math.radians(angle)) * dist
        z = math.sin(math.radians(angle)) * dist
        y = random.uniform(-0.5, 0.5)
        
        if random.random() > 0.6:
            # Obstacle (Thwomp-like)
            obstacle = Entity(
                model='cube',
                color=color.gray,
                position=(x, y + 0.5, z),
                scale=(1.5, 1.5, 1.5),
                collider='box',
                texture='white_cube'
            )
            obstacles.append(obstacle)
            track_entities.append(obstacle)
        else:
            # Item box (N64 style)
            item = Entity(
                model='cube',
                color=n64_yellow,
                position=(x, y + 0.5, z),
                scale=(1, 1, 1),
                collider='box',
                texture='white_cube'
            )
            items.append(item)
            track_entities.append(item)
    
    # Add some decorative elements (trees, etc.)
    for i in range(20):
        angle = random.randint(0, 360)
        dist = random.uniform(30, 40)
        x = math.cos(math.radians(angle)) * dist
        z = math.sin(math.radians(angle)) * dist
        y = -0.5
        
        # Use cube for tree trunk (since 'cylinder' may not exist)
        tree = Entity(
            model='cube',
            color=n64_green,
            position=(x, y + 1.5, z),
            scale=(0.5, 3, 0.5)
        )
        track_entities.append(tree)
    
    return track_entities, obstacles, items

# Improved Kart class with N64-style physics
class Kart(Entity):
    def __init__(self, **kwargs):
        super().__init__()
        # N64-style kart model (simplified)
        self.model = 'cube'
        self.color = n64_red
        self.scale = (1.5, 0.8, 2.5)
        self.position = (0, 0, 0)
        self.rotation = (0, 0, 0)
        self.collider = 'box'
        
        # N64-style physics
        self.speed = 0
        self.max_speed = 25
        self.acceleration = 0.8
        self.steering_speed = 3
        self.drift_factor = 0.9
        self.is_drifting = False
        self.has_item = False
        self.item_type = None
        self.drift_boost = 0
        self.gravity = 15
        self.grounded = True
        
        # Add wheels for visual effect — using cubes rotated to look like wheels
        self.wheels = []
        wheel_positions = [(-0.7, -0.4, 1), (0.7, -0.4, 1), (-0.7, -0.4, -1), (0.7, -0.4, -1)]
        for pos in wheel_positions:
            wheel = Entity(
                model='cube',  # <-- 'cylinder' not available by default
                color=color.black,
                position=pos,
                scale=(0.3, 0.1, 0.3),
                rotation=(90, 0, 0),  # lay it flat like a wheel
                parent=self
            )
            self.wheels.append(wheel)
        
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def update(self):
        # Movement controls - N64 style handling
        if held_keys['w'] or held_keys['up arrow']:
            self.speed += self.acceleration * time.dt
        elif held_keys['s'] or held_keys['down arrow']:
            self.speed -= self.acceleration * time.dt * 2  # Faster braking
        else:
            # Gradual slowdown (N64 style)
            self.speed *= 0.98
            
        # Limit speed
        self.speed = max(-self.max_speed/2, min(self.speed, self.max_speed + self.drift_boost))
        
        # Steering - N64 style (more responsive at high speeds)
        steering_power = self.steering_speed * (1 - abs(self.speed)/self.max_speed * 0.7) * 50 * time.dt
        if held_keys['a'] or held_keys['left arrow']:
            self.rotation_y -= steering_power
        if held_keys['d'] or held_keys['right arrow']:
            self.rotation_y += steering_power
            
        # Drifting - N64 style (with boost accumulation)
        if held_keys['space'] and abs(self.speed) > self.max_speed/3 and self.grounded:
            self.is_drifting = True
            self.color = n64_purple
            self.drift_boost += 2 * time.dt
            # Visual drift effect
            for wheel in self.wheels:
                wheel.color = color.orange
        else:
            if self.is_drifting and self.drift_boost > 0:
                # Apply drift boost
                self.speed += self.drift_boost
                self.drift_boost = 0
            self.is_drifting = False
            self.color = n64_red
            for wheel in self.wheels:
                wheel.color = color.black
            
        # Move the kart
        self.position += self.forward * self.speed * time.dt
        
        # Simple gravity
        if not self.grounded:
            self.y -= self.gravity * time.dt
            
        # Ground detection
        ground_ray = raycast(self.position, self.down, distance=1, ignore=[self])
        if ground_ray.hit:
            self.grounded = True
            self.y = ground_ray.world_point.y + 0.5
        else:
            self.grounded = False
            
        # Check for collisions with obstacles
        for obstacle in obstacles:
            if distance(self, obstacle) < 2.5:
                self.speed *= 0.3  # Slow down when hitting obstacle
                obstacle.shake(duration=0.5, speed=10)
                
        # Use item if player has one
        if self.has_item and held_keys['e']:
            self.use_item()

    def use_item(self):
        if self.item_type == "mushroom":
            self.speed += 15  # Big boost speed
            invoke(setattr, self, 'speed', self.speed - 15, delay=1.5)  # Remove boost after 1.5 seconds
            # Visual effect
            mushroom_effect = Entity(
                model='sphere',
                color=n64_red,
                position=self.position + (0, 1, 0),
                scale=0.5,
                billboard=True
            )
            destroy(mushroom_effect, delay=0.5)
        self.has_item = False
        self.item_type = None
        item_text.text = 'Item: None'

# N64-style camera follow system
def camera_follow():
    if player:
        # N64-style camera that follows behind the kart
        target_pos = player.position - player.forward * 8 + Vec3(0, 4, 0)
        camera.position = lerp(camera.position, target_pos, 6 * time.dt)
        camera.rotation_x = lerp(camera.rotation_x, 15, 6 * time.dt)
        camera.look_at(player.position, axis='up')

# Create N64-style skybox — FIXED: no linear_gradient
def create_n64_sky():
    # Simple sky with solid color (N64 blue)
    sky = Entity(
        model='sphere',
        double_sided=True,
        scale=500,
        color=n64_blue,  # ✅ FIXED: replaced invalid linear_gradient
        texture='sky_default'
    )
    return sky

# Create game elements
track, obstacles, items = generate_track()
player = Kart()
sky = create_n64_sky()

# N64-style UI elements
speed_text = Text(
    text='SPEED: 0', 
    position=(-0.8, 0.4), 
    scale=2,
    color=n64_yellow,
    background=True
)
item_text = Text(
    text='ITEM: NONE', 
    position=(-0.8, 0.3), 
    scale=2,
    color=n64_yellow,
    background=True
)

# Lap counter
lap_count = 0
lap_text = Text(
    text=f'LAP: {lap_count}/3', 
    position=(0.7, 0.4), 
    scale=2,
    color=n64_yellow,
    background=True
)

# Update function
def update():
    camera_follow()
    if player:
        speed_text.text = f'SPEED: {int(abs(player.speed))}'
    
    # Check for item collisions
    for item in items:
        if distance(player, item) < 2:
            player.has_item = True
            player.item_type = "mushroom"
            item_text.text = 'ITEM: MUSHROOM (E TO USE)'
            # Reposition the item
            angle = random.randint(0, 360)
            dist = random.uniform(15, 22)
            x = math.cos(math.radians(angle)) * dist
            z = math.sin(math.radians(angle)) * dist
            y = random.uniform(-0.5, 0.5)
            item.position = (x, y + 0.5, z)
            
            # Visual effect
            item.shake(duration=0.3, speed=5)

# Start game
def input(key):
    if key == 'r':
        player.position = (0, 0, 0)
        player.speed = 0
        player.rotation = (0, 0, 0)
    if key == 'escape':
        app.quit()

# N64-style instructions
instructions = Text(
    text='CONTROLS: WASD/ARROWS TO MOVE, SPACE TO DRIFT, R TO RESET, E TO USE ITEM',
    position=(-0.8, -0.4),
    scale=1.2,
    color=n64_yellow,
    background=True
)

# N64-style title
title = Text(
    text='MARIO KART 64',
    position=(0, 0.35),
    scale=3,
    color=n64_red,
    background=True
)

# Apply N64-style shader to all entities that support it
for entity in scene.entities:
    if hasattr(entity, 'shader') and entity.model:  # Only apply if entity has model & shader attr
        entity.shader = lit_with_shadows_shader

app.run()
