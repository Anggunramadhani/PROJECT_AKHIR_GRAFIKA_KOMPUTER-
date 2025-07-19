import pygame
import numpy as np
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import vbo
import sys

class Cube3D:
    def __init__(self):
        # Vertices kubus (x, y, z, nx, ny, nz) - posisi dan normal
        self.vertices = np.array([
            # Front face (z = 1)
            [-1, -1,  1,  0,  0,  1],
            [ 1, -1,  1,  0,  0,  1],
            [ 1,  1,  1,  0,  0,  1],
            [-1,  1,  1,  0,  0,  1],
            
            # Back face (z = -1)
            [-1, -1, -1,  0,  0, -1],
            [-1,  1, -1,  0,  0, -1],
            [ 1,  1, -1,  0,  0, -1],
            [ 1, -1, -1,  0,  0, -1],
            
            # Top face (y = 1)
            [-1,  1, -1,  0,  1,  0],
            [-1,  1,  1,  0,  1,  0],
            [ 1,  1,  1,  0,  1,  0],
            [ 1,  1, -1,  0,  1,  0],
            
            # Bottom face (y = -1)
            [-1, -1, -1,  0, -1,  0],
            [ 1, -1, -1,  0, -1,  0],
            [ 1, -1,  1,  0, -1,  0],
            [-1, -1,  1,  0, -1,  0],
            
            # Right face (x = 1)
            [ 1, -1, -1,  1,  0,  0],
            [ 1,  1, -1,  1,  0,  0],
            [ 1,  1,  1,  1,  0,  0],
            [ 1, -1,  1,  1,  0,  0],
            
            # Left face (x = -1)
            [-1, -1, -1, -1,  0,  0],
            [-1, -1,  1, -1,  0,  0],
            [-1,  1,  1, -1,  0,  0],
            [-1,  1, -1, -1,  0,  0],
        ], dtype=np.float32)
        
        # Indices untuk faces (triangles)
        self.indices = np.array([
            # Front face
            0, 1, 2,   0, 2, 3,
            # Back face
            4, 5, 6,   4, 6, 7,
            # Top face
            8, 9, 10,  8, 10, 11,
            # Bottom face
            12, 13, 14, 12, 14, 15,
            # Right face
            16, 17, 18, 16, 18, 19,
            # Left face
            20, 21, 22, 20, 22, 23,
        ], dtype=np.uint32)
        
        # Transform properties
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.rotation_z = 0.0
        self.translation_x = 0.0
        self.translation_y = 0.0
        self.translation_z = -5.0
        
    def draw(self):
        glPushMatrix()
        
        # Apply transformations
        glTranslatef(self.translation_x, self.translation_y, self.translation_z)
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)
        glRotatef(self.rotation_z, 0, 0, 1)
        
        # Draw cube using vertices and indices
        glBegin(GL_TRIANGLES)
        for i in range(0, len(self.indices), 3):
            for j in range(3):
                vertex_index = self.indices[i + j]
                vertex = self.vertices[vertex_index]
                
                # Set normal for lighting
                glNormal3f(vertex[3], vertex[4], vertex[5])
                # Set vertex position
                glVertex3f(vertex[0], vertex[1], vertex[2])
        glEnd()
        
        glPopMatrix()

class Camera:
    def __init__(self):
        self.position = [0.0, 0.0, 10.0]
        self.target = [0.0, 0.0, 0.0]
        self.up = [0.0, 1.0, 0.0]
        self.fov = 45.0
        self.near = 0.1
        self.far = 100.0
        
    def setup_projection(self, width, height):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, width/height, self.near, self.far)
        
    def setup_view(self):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(self.position[0], self.position[1], self.position[2],
                  self.target[0], self.target[1], self.target[2],
                  self.up[0], self.up[1], self.up[2])

class PhongLighting:
    def __init__(self):
        # Ambient light
        self.ambient_color = [0.2, 0.2, 0.2, 1.0]
        
        # Diffuse light
        self.diffuse_position = [5.0, 5.0, 5.0, 1.0]  # Positional light
        self.diffuse_color = [0.8, 0.8, 0.8, 1.0]
        
        # Specular light
        self.specular_color = [1.0, 1.0, 1.0, 1.0]
        
        # Material properties
        self.material_ambient = [0.2, 0.2, 0.8, 1.0]
        self.material_diffuse = [0.3, 0.3, 1.0, 1.0]
        self.material_specular = [1.0, 1.0, 1.0, 1.0]
        self.material_shininess = 50.0
        
    def setup(self):
        # Enable lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_COLOR_MATERIAL)
        
        # Set ambient light
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, self.ambient_color)
        
        # Set diffuse light
        glLightfv(GL_LIGHT0, GL_POSITION, self.diffuse_position)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, self.diffuse_color)
        glLightfv(GL_LIGHT0, GL_SPECULAR, self.specular_color)
        
        # Set material properties
        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, self.material_ambient)
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, self.material_diffuse)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, self.material_specular)
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, self.material_shininess)
        
        # Enable smooth shading (Gouraud)
        glShadeModel(GL_SMOOTH)

class Viewer3D:
    def __init__(self):
        pygame.init()
        self.width = 1024
        self.height = 768
        self.screen = pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("3D Object Visualization - Phong Lighting")
        
        # Initialize components
        self.cube = Cube3D()
        self.camera = Camera()
        self.lighting = PhongLighting()
        
        # Mouse control
        self.mouse_dragging = False
        self.last_mouse_pos = (0, 0)
        
        # Setup OpenGL
        self.setup_opengl()
        
    def setup_opengl(self):
        # Clear color
        glClearColor(0.1, 0.1, 0.1, 1.0)
        
        # Setup camera projection
        self.camera.setup_projection(self.width, self.height)
        
        # Setup lighting
        self.lighting.setup()
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            elif event.type == pygame.KEYDOWN:
                # Keyboard transformations
                if event.key == pygame.K_w:
                    self.cube.translation_z += 0.5
                elif event.key == pygame.K_s:
                    self.cube.translation_z -= 0.5
                elif event.key == pygame.K_a:
                    self.cube.translation_x -= 0.5
                elif event.key == pygame.K_d:
                    self.cube.translation_x += 0.5
                elif event.key == pygame.K_q:
                    self.cube.translation_y += 0.5
                elif event.key == pygame.K_e:
                    self.cube.translation_y -= 0.5
                    
                # Rotation with arrow keys
                elif event.key == pygame.K_UP:
                    self.cube.rotation_x += 5
                elif event.key == pygame.K_DOWN:
                    self.cube.rotation_x -= 5
                elif event.key == pygame.K_LEFT:
                    self.cube.rotation_y -= 5
                elif event.key == pygame.K_RIGHT:
                    self.cube.rotation_y += 5
                elif event.key == pygame.K_z:
                    self.cube.rotation_z += 5
                elif event.key == pygame.K_x:
                    self.cube.rotation_z -= 5
                    
                # Reset transformations
                elif event.key == pygame.K_r:
                    self.cube.rotation_x = 0
                    self.cube.rotation_y = 0
                    self.cube.rotation_z = 0
                    self.cube.translation_x = 0
                    self.cube.translation_y = 0
                    self.cube.translation_z = -5
                    
                # Change lighting position
                elif event.key == pygame.K_1:
                    self.lighting.diffuse_position[0] += 1
                elif event.key == pygame.K_2:
                    self.lighting.diffuse_position[0] -= 1
                elif event.key == pygame.K_3:
                    self.lighting.diffuse_position[1] += 1
                elif event.key == pygame.K_4:
                    self.lighting.diffuse_position[1] -= 1
                elif event.key == pygame.K_5:
                    self.lighting.diffuse_position[2] += 1
                elif event.key == pygame.K_6:
                    self.lighting.diffuse_position[2] -= 1
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.mouse_dragging = True
                    self.last_mouse_pos = pygame.mouse.get_pos()
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_dragging = False
                    
            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_dragging:
                    mouse_pos = pygame.mouse.get_pos()
                    dx = mouse_pos[0] - self.last_mouse_pos[0]
                    dy = mouse_pos[1] - self.last_mouse_pos[1]
                    
                    # Rotate based on mouse movement
                    self.cube.rotation_y += dx * 0.5
                    self.cube.rotation_x += dy * 0.5
                    
                    self.last_mouse_pos = mouse_pos
                    
        return True
    
    def render(self):
        # Clear buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Setup camera view
        self.camera.setup_view()
        
        # Update lighting position
        glLightfv(GL_LIGHT0, GL_POSITION, self.lighting.diffuse_position)
        
        # Draw cube
        self.cube.draw()
        
        # Swap buffers
        pygame.display.flip()
    
    def print_controls(self):
        print ("\n=== 3D OBJECT VISUALIZATION CONTROLS ===")
        print("TRANSFORMASI OBJEK:")
        print("  W/S     - Gerak maju/mundur (translasi Z)")
        print("  A/D     - Gerak kiri/kanan (translasi X)")
        print("  Q/E     - Gerak atas/bawah (translasi Y)")
        print("  Panah Atas/Bawah - Rotasi X")
        print("  Panah Kiri/Kanan - Rotasi Y")
        print("  Z/X     - Rotasi Z")
        print("  Mouse   - Drag untuk rotasi")
        print("\nPENCERAHYAAN:")
        print("  1/2     - Gerak cahaya X+/-")
        print("  3/4     - Gerak cahaya Y+/-")
        print("  5/6     - Gerak cahaya Z+/-")
        print("\nLAINNYA:")
        print("  R       - Reset semua transformasi")
        print("  ESC     - Keluar")
        print("=========================================\n")
    
    def run(self):
        self.print_controls()
        clock = pygame.time.Clock()
        running = True
        
        while running:
            running = self.handle_events()
            self.render()
            clock.tick(60)  # 60 FPS
            
        pygame.quit()
        sys.exit()

# Load OBJ file function (bonus feature)
def load_obj_file(filename):
    """
    Load vertices dan faces dari file .obj
    Return: vertices array, faces array
    """
    vertices = []
    faces = []
    normals = []
    
    try:
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if line.startswith('v '):  # Vertex
                    parts = line.split()
                    vertex = [float(parts[1]), float(parts[2]), float(parts[3])]
                    vertices.append(vertex)
                elif line.startswith('vn '):  # Normal
                    parts = line.split()
                    normal = [float(parts[1]), float(parts[2]), float(parts[3])]
                    normals.append(normal)
                elif line.startswith('f '):  # Face
                    parts = line.split()[1:]  # Skip 'f'
                    face_indices = []
                    for part in parts:
                        # Handle format: vertex/texture/normal or vertex//normal
                        indices = part.split('/')
                        vertex_idx = int(indices[0]) - 1  # OBJ indices start from 1
                        face_indices.append(vertex_idx)
                    faces.append(face_indices)
                    
        print(f"Loaded {len(vertices)} vertices and {len(faces)} faces from {filename}")
        return vertices, faces, normals
        
    except FileNotFoundError:
        print(f"File {filename} tidak ditemukan. Menggunakan kubus default.")
        return None, None, None

if __name__ == "__main__":
    print("Starting 3D Object Visualization...")
    print("Implementasi fitur:")
    print("[OK] Objek 3D (Kubus dengan vertex dan face manual)")
    print("[OK] Transformasi (Translasi, Rotasi dengan keyboard/mouse)")
    print("[OK] Model Pencahayaan Phong (Ambient, Diffuse, Specular)")
    print("[OK] Kamera dengan proyeksi perspektif (gluPerspective, gluLookAt)")
    print("[OK] Bonus: Fungsi load file .obj")
    
    # Uncomment baris berikut untuk load file .obj
    # vertices, faces, normals = load_obj_file("model.obj")
    
    viewer = Viewer3D()
    viewer.run()