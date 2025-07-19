import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import math

class Shape:
    def _init_(self, shape_type, points, color, thickness=1):
        self.type = shape_type
        self.original_points = np.array(points, dtype=np.float32)
        self.transformed_points = np.array(points, dtype=np.float32)
        self.color = color
        self.thickness = thickness
        self.selected = False
        self.drag_offset = [0, 0]
        self.rotation_angle = 0
        self.scale_factor = [1.0, 1.0]
        self.transform_matrix = np.identity(3)
        
    def update_transform(self):
        """Update all transformations"""
        # Reset to original points
        self.transformed_points = self.original_points.copy()
        
        # Apply transformations in order: scale -> rotate -> translate
        transform = np.identity(3)
        
        # 1. Scaling
        scale_mat = np.array([
            [self.scale_factor[0], 0, 0],
            [0, self.scale_factor[1], 0],
            [0, 0, 1]
        ])
        transform = np.dot(scale_mat, transform)
        
        # 2. Rotation
        angle_rad = math.radians(self.rotation_angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        center = self.get_center()
        
        rotation_mat = np.array([
            [cos_a, -sin_a, center[0]*(1-cos_a) + center[1]*sin_a],
            [sin_a, cos_a, center[1]*(1-cos_a) - center[0]*sin_a],
            [0, 0, 1]
        ])
        transform = np.dot(rotation_mat, transform)
        
        # 3. Translation
        translation_mat = np.array([
            [1, 0, self.drag_offset[0]],
            [0, 1, self.drag_offset[1]],
            [0, 0, 1]
        ])
        transform = np.dot(translation_mat, transform)
        
        # Apply final transformation
        self.transform_matrix = transform
        self.apply_transform()
    
    def apply_transform(self):
        """Apply current transformation matrix to points"""
        for i in range(len(self.original_points)):
            point = np.append(self.original_points[i], 1)  # Convert to homogeneous
            transformed = np.dot(self.transform_matrix, point)
            self.transformed_points[i] = transformed[:2]
    
    def get_center(self):
        """Get center of original points"""
        return np.mean(self.original_points, axis=0)
    
    def draw(self):
        glColor3f(*self.color)
        glLineWidth(self.thickness)
        
        if self.type == 'point':
            glPointSize(self.thickness * 2)
            glBegin(GL_POINTS)
            for point in self.transformed_points:
                glVertex2f(point[0], point[1])
            glEnd()
        elif self.type == 'line':
            glBegin(GL_LINES)
            for point in self.transformed_points:
                glVertex2f(point[0], point[1])
            glEnd()
        elif self.type in ['rectangle', 'ellipse']:
            glBegin(GL_LINE_LOOP)
            for point in self.transformed_points:
                glVertex2f(point[0], point[1])
            glEnd()
        
        # Draw selection handles
        if self.selected:
            self.draw_selection_handles()
    
    def draw_selection_handles(self):
        """Draw transformation handles when selected"""
        glColor3f(1.0, 1.0, 0.0)  # Yellow
        glPointSize(8)
        glBegin(GL_POINTS)
        
        # Draw center point
        center = self.get_transformed_center()
        glVertex2f(center[0], center[1])
        
        # Draw scale handles
        bounds = self.get_bounding_box()
        glVertex2f(bounds[0], bounds[1])  # Top-left
        glVertex2f(bounds[2], bounds[3])  # Bottom-right
        
        glEnd()
    
    def get_transformed_center(self):
        """Get center after transformations"""
        return np.mean(self.transformed_points, axis=0)
    
    def get_bounding_box(self):
        """Get bounding box of transformed shape (min_x, min_y, max_x, max_y)"""
        if len(self.transformed_points) == 0:
            return (0, 0, 0, 0)
        min_x = min(p[0] for p in self.transformed_points)
        min_y = min(p[1] for p in self.transformed_points)
        max_x = max(p[0] for p in self.transformed_points)
        max_y = max(p[1] for p in self.transformed_points)
        return (min_x, min_y, max_x, max_y)
    
    def is_point_inside(self, point):
        """Check if point is inside shape (simple bounding box check)"""
        bounds = self.get_bounding_box()
        return bounds[0] <= point[0] <= bounds[2] and bounds[1] <= point[1] <= bounds[3]

class Graphics2DEditor:
    def _init_(self):
        pygame.init()
        self.screen_width = 1200
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("2D Editor with Transformations")
        
        glClearColor(0.1, 0.1, 0.15, 1.0)
        gluOrtho2D(0, self.screen_width, 0, self.screen_height)
        
        self.shapes = []
        self.current_tool = 'select'
        self.current_color = (1.0, 1.0, 1.0)
        self.line_thickness = 1.0
        self.temp_points = []
        self.selected_shape = None
        self.drag_start = None
        self.transform_mode = None  # 'move', 'rotate', 'scale'
        
        self.color_palette = [
            (1.0, 1.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
            (1.0, 1.0, 0.0), (1.0, 0.0, 1.0), (0.0, 1.0, 1.0), (0.5, 0.5, 0.5)
        ]
        
        self.font = pygame.font.SysFont('Arial', 16)
        self.print_instructions()
    
    def print_instructions(self):
        print("=== INSTRUCTIONS ===")
        print("DRAWING: P(Point) L(Line) R(Rectangle) E(Ellipse)")
        print("SELECT: S | CLEAR: C")
        print("COLORS: 1-8 | THICKNESS: +/-")
        print("MOUSE DRAG:")
        print("  - Drag center: Move")
        print("  - Drag corner: Scale")
        print("  - Drag outside: Rotate")
        print("KEYBOARD:")
        print("  Arrows: Move | Q/W: Rotate | A/Z: Scale")

    def handle_mouse_down(self, x, y):
        gl_y = self.screen_height - y
        self.drag_start = (x, gl_y)
        
        if self.current_tool == 'select' and self.selected_shape:
            center = self.selected_shape.get_transformed_center()
            bounds = self.selected_shape.get_bounding_box()
            
            # Check what part of shape is being dragged
            if math.dist((x, gl_y), center) < 10:
                self.transform_mode = 'move'
            elif math.dist((x, gl_y), (bounds[0], bounds[1])) < 10 or math.dist((x, gl_y), (bounds[2], bounds[3])) < 10:
                self.transform_mode = 'scale'
            else:
                self.transform_mode = 'rotate'
        else:
            self.transform_mode = None
    
    def handle_mouse_up(self):
        self.drag_start = None
        self.transform_mode = None
    
    def handle_mouse_drag(self, x, y):
        if not self.drag_start or not self.selected_shape:
            return
            
        gl_y = self.screen_height - y
        dx = x - self.drag_start[0]
        dy = gl_y - self.drag_start[1]
        
        if self.transform_mode == 'move':
            self.selected_shape.drag_offset[0] += dx
            self.selected_shape.drag_offset[1] += dy
            self.selected_shape.update_transform()
        
        elif self.transform_mode == 'rotate':
            center = self.selected_shape.get_transformed_center()
            angle = math.degrees(math.atan2(gl_y - center[1], x - center[0]) - 
                                 math.atan2(self.drag_start[1] - center[1], 
                                 self.drag_start[0] - center[0]))
            self.selected_shape.rotation_angle += angle
            self.selected_shape.update_transform()
        
        elif self.transform_mode == 'scale':
            scale_factor = 1 + dx * 0.01  # Adjust scaling sensitivity
            self.selected_shape.scale_factor[0] *= scale_factor
            self.selected_shape.scale_factor[1] *= scale_factor
            self.selected_shape.update_transform()
        
        self.drag_start = (x, gl_y)
    
    def create_shape(self, shape_type, points):
        if shape_type == 'point':
            return Shape('point', points, self.current_color, self.line_thickness)
        elif shape_type == 'line':
            return Shape('line', points, self.current_color, self.line_thickness)
        elif shape_type == 'rectangle':
            x1, y1 = points[0]
            x2, y2 = points[1]
            rect_points = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
            return Shape('rectangle', rect_points, self.current_color, self.line_thickness)
        elif shape_type == 'ellipse':
            cx = (points[0][0] + points[1][0]) / 2
            cy = (points[0][1] + points[1][1]) / 2
            rx = abs(points[1][0] - points[0][0]) / 2
            ry = abs(points[1][1] - points[0][1]) / 2
            
            ellipse_points = []
            for i in range(32):
                angle = 2 * math.pi * i / 32
                ellipse_points.append([cx + rx * math.cos(angle), cy + ry * math.sin(angle)])
            
            return Shape('ellipse', ellipse_points, self.current_color, self.line_thickness)
    
    def select_shape_at(self, x, y):
        for shape in reversed(self.shapes):  # Select top-most shape first
            if shape.is_point_inside((x, y)):
                if self.selected_shape:
                    self.selected_shape.selected = False
                self.selected_shape = shape
                shape.selected = True
                return True
        return False
    
    def render(self):
        glClear(GL_COLOR_BUFFER_BIT)
        
        # Draw all shapes
        for shape in self.shapes:
            shape.draw()
        
        # Draw temporary points (during creation)
        if self.temp_points:
            glColor3f(1.0, 0.0, 0.0)
            glPointSize(5)
            glBegin(GL_POINTS)
            for point in self.temp_points:
                glVertex2f(point[0], point[1])
            glEnd()
        
        # Draw instructions on screen
        self.draw_text("Tools: P(Point) L(Line) R(Rect) E(Ellipse) S(Select)", 10, 10)
        self.draw_text("Transform: Drag center(move) corner(scale) edge(rotate)", 10, 30)
        self.draw_text(f"Selected: {self.selected_shape.type if self.selected_shape else 'None'}", 10, 50)
        
        pygame.display.flip()
    
    def draw_text(self, text, x, y):
        """Draw text on screen using pygame"""
        text_surface = self.font.render(text, True, (255, 255, 255))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        glWindowPos2d(x, self.screen_height - y - 20)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(), 
                    GL_RGBA, GL_UNSIGNED_BYTE, text_data)
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    
                    # Tool selection
                    elif event.key == pygame.K_p:
                        self.current_tool = 'point'
                    elif event.key == pygame.K_l:
                        self.current_tool = 'line'
                    elif event.key == pygame.K_r:
                        self.current_tool = 'rectangle'
                    elif event.key == pygame.K_e:
                        self.current_tool = 'ellipse'
                    elif event.key == pygame.K_s:
                        self.current_tool = 'select'
                    
                    # Color selection
                    elif pygame.K_1 <= event.key <= pygame.K_8:
                        self.current_color = self.color_palette[event.key - pygame.K_1]
                    
                    # Thickness
                    elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                        self.line_thickness = min(10.0, self.line_thickness + 1)
                    elif event.key == pygame.K_MINUS:
                        self.line_thickness = max(1.0, self.line_thickness - 1)
                    
                    # Keyboard transformations
                    elif event.key == pygame.K_LEFT and self.selected_shape:
                        self.selected_shape.drag_offset[0] -= 10
                        self.selected_shape.update_transform()
                    elif event.key == pygame.K_RIGHT and self.selected_shape:
                        self.selected_shape.drag_offset[0] += 10
                        self.selected_shape.update_transform()
                    elif event.key == pygame.K_UP and self.selected_shape:
                        self.selected_shape.drag_offset[1] += 10
                        self.selected_shape.update_transform()
                    elif event.key == pygame.K_DOWN and self.selected_shape:
                        self.selected_shape.drag_offset[1] -= 10
                        self.selected_shape.update_transform()
                    elif event.key == pygame.K_q and self.selected_shape:
                        self.selected_shape.rotation_angle += 15
                        self.selected_shape.update_transform()
                    elif event.key == pygame.K_w and self.selected_shape:
                        self.selected_shape.rotation_angle -= 15
                        self.selected_shape.update_transform()
                    elif event.key == pygame.K_a and self.selected_shape:
                        self.selected_shape.scale_factor[0] *= 1.1
                        self.selected_shape.scale_factor[1] *= 1.1
                        self.selected_shape.update_transform()
                    elif event.key == pygame.K_z and self.selected_shape:
                        self.selected_shape.scale_factor[0] *= 0.9
                        self.selected_shape.scale_factor[1] *= 0.9
                        self.selected_shape.update_transform()
                    
                    # Clear
                    elif event.key == pygame.K_c:
                        self.shapes = []
                        self.selected_shape = None
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    gl_y = self.screen_height - event.pos[1]
                    
                    if event.button == 1:  # Left click
                        if self.current_tool == 'select':
                            if not self.select_shape_at(event.pos[0], gl_y):
                                self.selected_shape = None
                            self.handle_mouse_down(event.pos[0], event.pos[1])
                        else:
                            self.temp_points.append([event.pos[0], gl_y])
                            if (self.current_tool == 'point' or 
                                (self.current_tool in ['line', 'rectangle', 'ellipse'] and len(self.temp_points) == 2)):
                                new_shape = self.create_shape(self.current_tool, self.temp_points)
                                self.shapes.append(new_shape)
                                self.temp_points = []
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.handle_mouse_up()
                
                elif event.type == pygame.MOUSEMOTION:
                    if event.buttons[0]:  # Left mouse button held
                        self.handle_mouse_drag(event.pos[0], event.pos[1])
            
            self.render()
            clock.tick(60)
        
        pygame.quit()

if _name_ == "_main_":
    editor = Graphics2DEditor()
    editor.run()