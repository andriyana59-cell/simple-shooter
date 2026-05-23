from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import Point3, Vec3, TransformState
from direct.interval.IntervalGlobal import *
import random
import math

class SimpleShooter(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.setBackgroundColor(0.1, 0.1, 0.2)
        
        # Game variables
        self.score = 0
        self.health = 100
        self.bullets = []
        self.targets = []
        self.player_speed = 30
        self.bullet_speed = 100
        
        # Input handling
        self.keys = {'w': False, 'a': False, 's': False, 'd': False}
        self.accept('w', self.set_key, ['w', True])
        self.accept('w-up', self.set_key, ['w', False])
        self.accept('a', self.set_key, ['a', True])
        self.accept('a-up', self.set_key, ['a', False])
        self.accept('s', self.set_key, ['s', True])
        self.accept('s-up', self.set_key, ['s', False])
        self.accept('d', self.set_key, ['d', True])
        self.accept('d-up', self.set_key, ['d', False])
        self.accept('mouse1', self.shoot)
        
        # Setup scene
        self.setup_lighting()
        self.setup_player()
        self.setup_arena()
        self.setup_ui()
        
        # Spawn targets
        self.spawn_target()
        
        # Tasks
        self.taskMgr.add(self.update_task, "update")
        self.taskMgr.add(self.player_movement_task, "player_movement")
        self.taskMgr.add(self.bullet_update_task, "bullet_update")
        self.taskMgr.add(self.target_update_task, "target_update")
        self.taskMgr.add(self.spawn_target_task, "spawn_target")
    
    def set_key(self, key, value):
        self.keys[key] = value
    
    def setup_lighting(self):
        """Setup basic lighting"""
        from panda3d.core import AmbientLight, DirectionalLight
        
        # Ambient light
        amb_light = AmbientLight("ambient")
        amb_light.setColor((0.6, 0.6, 0.6, 1))
        self.render.attachNewNode(amb_light)
        self.render.setLight(self.render.attachNewNode(amb_light))
        
        # Directional light
        dir_light = DirectionalLight("directional")
        dir_light.setColor((1, 1, 1, 1))
        dir_light_node = self.render.attachNewNode(dir_light)
        dir_light_node.setP(-45)
        self.render.setLight(dir_light_node)
    
    def setup_player(self):
        """Setup player character"""
        from panda3d.core import CardMaker
        
        # Create simple player (cube)
        self.player = self.loader.loadModel("box")
        self.player.setScale(0.5, 2, 0.5)
        self.player.setPos(0, 0, 0)
        self.player.reparentTo(self.render)
        self.player.setColor(0, 1, 0, 1)  # Green
        
        # Player velocity
        self.player_velocity = Vec3(0, 0, 0)
    
    def setup_arena(self):
        """Setup game arena"""
        # Floor
        floor = self.loader.loadModel("box")
        floor.setScale(50, 0.5, 50)
        floor.setPos(0, -3, 0)
        floor.reparentTo(self.render)
        floor.setColor(0.5, 0.5, 0.5, 1)
        
        # Walls
        wall_positions = [
            (0, 5, 50),    # back
            (0, 5, -50),   # front
            (50, 5, 0),    # right
            (-50, 5, 0),   # left
        ]
        
        for pos in wall_positions:
            wall = self.loader.loadModel("box")
            if pos[2] != 0:
                wall.setScale(50, 10, 1)
            else:
                wall.setScale(1, 10, 50)
            wall.setPos(pos)
            wall.reparentTo(self.render)
            wall.setColor(0.3, 0.3, 0.3, 1)
    
    def setup_ui(self):
        """Setup UI text"""
        from panda3d.core import TextNode
        
        # Score text
        self.score_text = TextNode("score")
        self.score_text.setText("Score: 0")
        self.score_text.setTextColor(1, 1, 1, 1)
        score_np = self.aspect2d.attachNewNode(self.score_text)
        score_np.setPos(-1.3, 0.9, 0)
        score_np.setScale(0.06)
        
        # Health text
        self.health_text = TextNode("health")
        self.health_text.setText("Health: 100")
        self.health_text.setTextColor(1, 0, 0, 1)
        health_np = self.aspect2d.attachNewNode(self.health_text)
        health_np.setPos(-1.3, 0.8, 0)
        health_np.setScale(0.06)
    
    def shoot(self):
        """Create a bullet"""
        bullet_pos = self.player.getPos() + Vec3(0, 1, 0)
        bullet_dir = self.render.getRelativePoint(self.camera, Point3(0, 0, -1))
        bullet_dir = (bullet_dir - bullet_pos).normalized()
        
        bullet = self.loader.loadModel("box")
        bullet.setScale(0.2, 0.2, 1)
        bullet.setPos(bullet_pos)
        bullet.reparentTo(self.render)
        bullet.setColor(1, 1, 0, 1)  # Yellow
        
        self.bullets.append({
            'model': bullet,
            'pos': bullet_pos,
            'dir': bullet_dir,
            'lifetime': 10
        })
    
    def spawn_target(self):
        """Spawn a target"""
        x = random.uniform(-40, 40)
        z = random.uniform(-40, 40)
        
        target = self.loader.loadModel("box")
        target.setScale(1, 1, 1)
        target.setPos(x, 1, z)
        target.reparentTo(self.render)
        target.setColor(1, 0, 0, 1)  # Red
        
        self.targets.append({
            'model': target,
            'health': 1,
            'pos': Point3(x, 1, z)
        })
    
    def set_key(self, key, value):
        self.keys[key] = value
    
    def player_movement_task(self, task):
        """Handle player movement"""
        dt = globalClock.getDt()
        movement = Vec3(0, 0, 0)
        
        if self.keys['w']:
            movement += self.render.getRelativePoint(self.camera, Point3(0, 0, -1)) - self.render.getRelativePoint(self.camera, Point3(0, 0, 0))
        if self.keys['s']:
            movement += self.render.getRelativePoint(self.camera, Point3(0, 0, 1)) - self.render.getRelativePoint(self.camera, Point3(0, 0, 0))
        if self.keys['a']:
            movement += self.render.getRelativePoint(self.camera, Point3(-1, 0, 0)) - self.render.getRelativePoint(self.camera, Point3(0, 0, 0))
        if self.keys['d']:
            movement += self.render.getRelativePoint(self.camera, Point3(1, 0, 0)) - self.render.getRelativePoint(self.camera, Point3(0, 0, 0))
        
        if movement.length() > 0:
            movement = movement.normalized()
            movement *= self.player_speed * dt
            
            new_pos = self.player.getPos() + movement
            
            # Clamp to arena
            new_pos.setX(max(-45, min(45, new_pos.getX())))
            new_pos.setZ(max(-45, min(45, new_pos.getZ())))
            
            self.player.setPos(new_pos)
        
        # Camera follows player
        camera_dist = 15
        camera_height = 8
        self.camera.setPos(self.player.getX(), self.player.getY() + camera_height, self.player.getZ() + camera_dist)
        self.camera.lookAt(self.player.getX(), self.player.getY() + 2, self.player.getZ())
        
        return Task.cont
    
    def bullet_update_task(self, task):
        """Update bullets"""
        dt = globalClock.getDt()
        
        for bullet in self.bullets[:]:
            bullet['pos'] += bullet['dir'] * self.bullet_speed * dt
            bullet['model'].setPos(bullet['pos'])
            bullet['lifetime'] -= dt
            
            # Remove if out of bounds or lifetime expired
            if bullet['lifetime'] <= 0 or bullet['pos'].length() > 100:
                bullet['model'].removeNode()
                self.bullets.remove(bullet)
                continue
            
            # Check collision with targets
            for target in self.targets[:]:
                distance = (bullet['pos'] - target['model'].getPos()).length()
                if distance < 2:
                    target['health'] -= 1
                    if target['health'] <= 0:
                        target['model'].removeNode()
                        self.targets.remove(target)
                        self.score += 10
                    
                    bullet['model'].removeNode()
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    break
        
        return Task.cont
    
    def target_update_task(self, task):
        """Update targets"""
        for target in self.targets:
            # Targets look at player
            target['model'].lookAt(self.player)
        
        return Task.cont
    
    def spawn_target_task(self, task):
        """Spawn new targets periodically"""
        if len(self.targets) < 3:
            self.spawn_target()
        return task.again(2)
    
    def update_task(self, task):
        """Update UI and game state"""
        self.score_text.setText(f"Score: {self.score}")
        self.health_text.setText(f"Health: {self.health}")
        
        return Task.cont

game = SimpleShooter()
game.run()
