import numpy as np
from moviepy import VideoClip, AudioFileClip
from moviepy.video.tools.drawing import color_gradient
from moviepy.video.tools.drawing import color_gradient
import json
import math
from PIL import Image, ImageDraw, ImageFont
import os

# Load audio analysis
with open('audio_analysis.json', 'r') as f:
    audio_data = json.load(f)

duration = audio_data['duration']  # 107.91 seconds
beat_times = audio_data['beat_times']
peak_times = audio_data['peak_times']
onset_times = audio_data['onset_times']

print(f"Video duration: {duration:.2f}s")
print(f"Beats: {len(beat_times)}")
print(f"Energy peaks: {len(peak_times)}")

# ============================================================
# DESIGN SYSTEM - NewEra AI Agent Brand
# ============================================================

# Color palette - High contrast, minimal
COLORS = {
    'bg_black': (10, 10, 12),        # Near black
    'bg_dark': (18, 18, 22),         # Dark gray
    'fg_white': (250, 250, 252),     # Near white
    'fg_gray': (160, 160, 170),      # Mid gray
    'accent_cyan': (0, 220, 255),    # Electric cyan accent
    'accent_orange': (255, 140, 0),  # Warm orange accent
    'accent_green': (80, 255, 120),  # Fresh green accent
    'metallic_silver': (190, 195, 205),
    'metallic_gold': (255, 215, 100),
}

# Typography settings
FONT_BOLD = "DejaVu-Sans-Bold"
FONT_REGULAR = "DejaVu-Sans"
FONT_LIGHT = "DejaVu-Sans-Light"

# Video settings
WIDTH = 1920
HEIGHT = 1080
FPS = 30

# ============================================================
# EASING FUNCTIONS
# ============================================================

def ease_out_cubic(t):
    return 1 - pow(1 - t, 3)

def ease_in_cubic(t):
    return t * t * t

def ease_in_out_cubic(t):
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

def ease_out_elastic(t):
    c4 = (2 * math.pi) / 3
    return 0 if t == 0 else 1 if t == 1 else pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1

def ease_out_expo(t):
    return 1 if t == 1 else 1 - pow(2, -10 * t)

def ease_out_back(t):
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

# ============================================================
# GRAPHIC PRIMITIVES
# ============================================================

def create_gradient_bg(width, height, color1, color2, angle=0):
    """Create a gradient background."""
    img = Image.new('RGB', (width, height), color1)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        ratio = y / height
        r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
        g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
        b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    return img

def create_radial_gradient(width, height, center_color, edge_color, center=None):
    """Create radial gradient."""
    if center is None:
        center = (width // 2, height // 2)
    img = Image.new('RGB', (width, height))
    pixels = img.load()
    max_dist = math.sqrt(center[0]**2 + center[1]**2)
    for y in range(height):
        for x in range(width):
            dist = math.sqrt((x - center[0])**2 + (y - center[1])**2)
            ratio = min(dist / max_dist, 1.0)
            r = int(center_color[0] * (1 - ratio) + edge_color[0] * ratio)
            g = int(center_color[1] * (1 - ratio) + edge_color[1] * ratio)
            b = int(center_color[2] * (1 - ratio) + edge_color[2] * ratio)
            pixels[x, y] = (r, g, b)
    return img

def draw_rounded_rect(draw, bbox, radius, fill, outline=None, width=1):
    """Draw rounded rectangle."""
    x1, y1, x2, y2 = bbox
    draw.rounded_rectangle(bbox, radius=radius, fill=fill, outline=outline, width=width)

def create_text_image(text, font_path, font_size, color, stroke_color=None, stroke_width=0):
    """Create text as transparent image."""
    # Use a temporary draw to measure
    temp_img = Image.new('RGBA', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()
    
    bbox = temp_draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    
    img = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), text, font=font, fill=color, stroke_fill=stroke_color, stroke_width=stroke_width)
    return img

def create_particle_field(width, height, num_particles=200, color=(255,255,255), alpha_range=(20, 100), size_range=(1, 3)):
    """Create particle field image."""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    np.random.seed(42)
    for _ in range(num_particles):
        x = np.random.randint(0, width)
        y = np.random.randint(0, height)
        size = np.random.uniform(*size_range)
        alpha = np.random.randint(*alpha_range)
        c = (*color[:3], alpha)
        draw.ellipse([x-size, y-size, x+size, y+size], fill=c)
    return img

# ============================================================
# ANIMATION CLASSES
# ============================================================

class AnimatedElement:
    def __init__(self, start_time, end_time, render_func):
        self.start_time = start_time
        self.end_time = end_time
        self.duration = end_time - start_time
        self.render_func = render_func
    
    def get_frame(self, t):
        if t < self.start_time or t > self.end_time:
            return None
        progress = (t - self.start_time) / self.duration
        return self.render_func(progress, t)

class TextReveal(AnimatedElement):
    def __init__(self, text, start_time, end_time, position, font_size, color, font_weight='bold',
                 animation_type='fade_slide_up', delay_per_char=0, **kwargs):
        self.text = text
        self.position = position
        self.font_size = font_size
        self.color = color
        self.font_weight = font_weight
        self.animation_type = animation_type
        self.delay_per_char = delay_per_char
        self.kwargs = kwargs
        super().__init__(start_time, end_time, self._render)
    
    def _render(self, progress, absolute_time):
        img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            if self.font_weight == 'bold':
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", self.font_size)
            elif self.font_weight == 'light':
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Light.ttf", self.font_size)
            else:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", self.font_size)
        except:
            font = ImageFont.load_default()
        
        x, y = self.position
        
        if self.animation_type == 'fade_slide_up':
            # Ease out cubic for smooth entrance
            eased = ease_out_cubic(progress)
            y_offset = int(40 * (1 - eased))
            alpha = int(255 * eased)
            text_color = (*self.color[:3], alpha)
            draw.text((x, y + y_offset), self.text, font=font, fill=text_color, anchor="mm")
        
        elif self.animation_type == 'scale_in':
            eased = ease_out_back(progress)
            scale = eased
            # Create text at larger size then scale
            text_img = create_text_image(self.text, "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                                       int(self.font_size * 1.2), self.color)
            new_size = (int(text_img.width * scale), int(text_img.height * scale))
            if new_size[0] > 0 and new_size[1] > 0:
                text_img = text_img.resize(new_size, Image.LANCZOS)
                img.paste(text_img, (x - text_img.width//2, y - text_img.height//2), text_img)
        
        elif self.animation_type == 'typewriter':
            chars_to_show = int(len(self.text) * progress)
            visible_text = self.text[:chars_to_show]
            draw.text((x, y), visible_text, font=font, fill=self.color, anchor="mm")
        
        elif self.animation_type == 'word_by_word':
            words = self.text.split(' ')
            words_to_show = int(len(words) * progress)
            visible_text = ' '.join(words[:words_to_show])
            draw.text((x, y), visible_text, font=font, fill=self.color, anchor="mm")
        
        return np.array(img)

class GeometricShape(AnimatedElement):
    def __init__(self, start_time, end_time, shape_type, position, size, color,
                 animation_type='fade_scale', rotation=0, **kwargs):
        self.shape_type = shape_type
        self.position = position
        self.size = size
        self.color = color
        self.animation_type = animation_type
        self.rotation = rotation
        self.kwargs = kwargs
        super().__init__(start_time, end_time, self._render)
    
    def _render(self, progress, absolute_time):
        img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        x, y = self.position
        
        if self.animation_type == 'fade_scale':
            eased = ease_out_cubic(progress)
            scale = eased
            alpha = int(255 * eased)
            c = (*self.color[:3], alpha)
            s = self.size * scale
        elif self.animation_type == 'pulse':
            # Pulse on beats
            pulse = (math.sin(progress * 20) + 1) / 2
            scale = 0.8 + 0.4 * pulse
            alpha = 255
            c = (*self.color[:3], alpha)
            s = self.size * scale
        elif self.animation_type == 'rotate':
            eased = ease_in_out_cubic(progress)
            scale = eased
            alpha = 255
            c = (*self.color[:3], alpha)
            s = self.size * scale
            rotation = self.rotation + progress * 360
        else:
            scale = 1
            alpha = 255
            c = (*self.color[:3], alpha)
            s = self.size
        
        if self.shape_type == 'circle':
            draw.ellipse([x - s, y - s, x + s, y + s], fill=c)
        elif self.shape_type == 'square':
            draw.rounded_rectangle([x - s, y - s, x + s, y + s], radius=s*0.1, fill=c)
        elif self.shape_type == 'line':
            length = s * 2
            angle = self.rotation if 'rotation' not in locals() else rotation
            x2 = x + length * math.cos(math.radians(angle))
            y2 = y + length * math.sin(math.radians(angle))
            draw.line([x, y, x2, y2], fill=c, width=max(1, int(s*0.1)))
        elif self.shape_type == 'ring':
            draw.ellipse([x - s, y - s, x + s, y + s], outline=c, width=max(1, int(s*0.05)))
        
        return np.array(img)

class ParticleBurst(AnimatedElement):
    def __init__(self, start_time, end_time, center, num_particles=50, color=(255,255,255), **kwargs):
        self.center = center
        self.num_particles = num_particles
        self.color = color
        self.particles = []
        np.random.seed(int(start_time * 1000) % 2**32)
        for _ in range(num_particles):
            angle = np.random.uniform(0, 2 * math.pi)
            speed = np.random.uniform(50, 300)
            size = np.random.uniform(2, 6)
            life = np.random.uniform(0.3, 1.0)
            self.particles.append({
                'angle': angle,
                'speed': speed,
                'size': size,
                'life': life,
                'start_delay': np.random.uniform(0, 0.1)
            })
        super().__init__(start_time, end_time, self._render)
    
    def _render(self, progress, absolute_time):
        img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx, cy = self.center
        
        for p in self.particles:
            p_progress = (progress - p['start_delay']) / p['life']
            if p_progress < 0 or p_progress > 1:
                continue
            eased = ease_out_cubic(p_progress)
            dist = p['speed'] * eased
            alpha = int(255 * (1 - eased))
            size = p['size'] * (1 - eased * 0.5)
            x = cx + dist * math.cos(p['angle'])
            y = cy + dist * math.sin(p['angle'])
            c = (*self.color[:3], alpha)
            draw.ellipse([x - size, y - size, x + size, y + size], fill=c)
        
        return np.array(img)

class GlitchText(AnimatedElement):
    def __init__(self, text, start_time, end_time, position, font_size, color, glitch_intensity=0.1, **kwargs):
        self.text = text
        self.position = position
        self.font_size = font_size
        self.color = color
        self.glitch_intensity = glitch_intensity
        super().__init__(start_time, end_time, self._render)
    
    def _render(self, progress, absolute_time):
        img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", self.font_size)
        except:
            font = ImageFont.load_default()
        
        x, y = self.position
        
        # Main text
        draw.text((x, y), self.text, font=font, fill=self.color, anchor="mm")
        
        # Glitch effect - random offset copies
        if progress > 0:
            np.random.seed(int(absolute_time * 100) % 2**32)
            for _ in range(3):
                offset_x = np.random.uniform(-self.glitch_intensity * self.font_size, 
                                            self.glitch_intensity * self.font_size)
                offset_y = np.random.uniform(-self.glitch_intensity * self.font_size, 
                                            self.glitch_intensity * self.font_size)
                glitch_color = (self.color[0], self.color[1], self.color[2], 100)
                draw.text((x + offset_x, y + offset_y), self.text, font=font, fill=glitch_color, anchor="mm")
        
        return np.array(img)

# ============================================================
# SCENE DEFINITIONS - Synced to Music
# ============================================================

def create_scene_elements():
    """Define all visual elements synced to the audio."""
    elements = []
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    
    # ---- SECTION 1: INTRO / LOGO REVEAL (0-15s) ----
    # Dark background with particle field
    elements.append(AnimatedElement(0, duration,
        lambda p, t: np.array(create_radial_gradient(WIDTH, HEIGHT, COLORS['bg_black'], COLORS['bg_dark']))))
    
    # Particle field (static)
    particles_static = create_particle_field(WIDTH, HEIGHT, 150, COLORS['fg_white'], (10, 60), (1, 2))
    elements.append(AnimatedElement(0, duration,
        lambda p, t: np.array(particles_static)))
    
    # NEWERA Logo - main reveal at first beat
    elements.append(TextReveal("NEWE" + "RA", 0.0, 4.0, (center_x, center_y - 60), 120, COLORS['fg_white'],
                  font_weight='bold', animation_type='fade_slide_up'))
    
    # "AI AGENT" subtitle
    elements.append(TextReveal("AI AGENT", 0.8, 4.0, (center_x, center_y + 60), 40, COLORS['accent_cyan'],
                  font_weight='light', animation_type='fade_slide_up'))
    
    # Accent line
    elements.append(GeometricShape(0.5, 3.0, 'line', (center_x, center_y + 10), 300, COLORS['accent_cyan'],
                       animation_type='fade_scale', rotation=0))
    
    # Ring expansion on first major peak (1.045s)
    elements.append(GeometricShape(1.04, 4.0, 'ring', (center_x, center_y), 200, COLORS['accent_cyan'],
                       animation_type='fade_scale'))
    
    # Secondary ring
    elements.append(GeometricShape(1.5, 4.0, 'ring', (center_x, center_y), 350, COLORS['fg_gray'],
                       animation_type='fade_scale'))
    
    # Particle burst at 3.35s peak
    elements.append(ParticleBurst(3.35, 5.0, (center_x, center_y), 80, COLORS['accent_cyan']))
    
    # "Founded by" text
    elements.append(TextReveal("Founded by", 4.5, 7.0, (center_x, center_y - 100), 28, COLORS['fg_gray'],
                  font_weight='regular', animation_type='fade_slide_up'))
    elements.append(TextReveal("Naman Soni", 5.0, 7.0, (center_x, center_y - 50), 48, COLORS['fg_white'],
                  font_weight='bold', animation_type='scale_in'))
    elements.append(TextReveal("newera.namansoni.in", 5.5, 7.0, (center_x, center_y + 30), 24, COLORS['accent_orange'],
                  font_weight='regular', animation_type='fade_slide_up'))
    
    # ---- SECTION 2: CAPABILITIES SHOWCASE (7-30s) ----
    # Each capability on beat
    capabilities = [
        ("Code Generation", "💻", 7.3, COLORS['accent_cyan']),
        ("Web Search", "🔍", 11.0, COLORS['accent_orange']),
        ("Image Generation", "🎨", 15.4, COLORS['accent_green']),
        ("Video Editing", "🎬", 18.7, COLORS['accent_cyan']),
        ("Audio Analysis", "🎵", 23.1, COLORS['accent_orange']),
        ("3D Generation", "🧊", 26.4, COLORS['accent_green']),
        ("Data Analysis", "📊", 30.3, COLORS['accent_cyan']),
        ("Automation", "⚡", 35.6, COLORS['accent_orange']),
    ]
    
    for i, (name, icon, start_t, color) in enumerate(capabilities):
        y_pos = center_y - 150 + (i % 4) * 100
        x_pos = center_x - 300 if i < 4 else center_x + 300
        
        # Card background
        elements.append(GeometricShape(start_t, start_t + 3.5, 'square', (x_pos, y_pos), 180, (*color[:3], 30),
                           animation_type='fade_scale'))
        
        # Icon/Title
        elements.append(TextReveal(name, start_t + 0.1, start_t + 3.0, (x_pos, y_pos - 30), 32, color,
                      font_weight='bold', animation_type='fade_slide_up'))
        
        # Pulse ring on beat
        elements.append(GeometricShape(start_t, start_t + 1.5, 'ring', (x_pos, y_pos), 150, color,
                           animation_type='fade_scale'))
    
    # ---- SECTION 3: TECHNICAL DEPTH (30-60s) ----
    # Code-like visualization
    code_lines = [
        "class NewEraAgent:",
        "    def __init__(self):",
        "        self.tools = [\"code\", \"web\", \"image\", \"video\", \"audio\", \"3d\"]",
        "        self.memory = VectorStore()",
        "        self.reasoning = ChainOfThought()",
        "    ",
        "    async def execute(self, task):",
        "        plan = self.reasoning.decompose(task)",
        "        for step in plan:",
        "            result = await self.tools.run(step)",
        "            self.memory.store(result)",
        "        return self.reasoning.synthesize()",
    ]
    
    for i, line in enumerate(code_lines):
        start = 30.3 + i * 0.8
        elements.append(TextReveal(line, start, min(start + 8, 55), 
                      (center_x - 400, center_y - 200 + i * 35), 22, COLORS['fg_gray'] if line.strip() else COLORS['fg_white'],
                      font_weight='regular' if not line.strip().startswith('class') else 'bold',
                      animation_type='typewriter', delay_per_char=0.02))
    
    # Flowing particles during code section
    for peak_t in peak_times:
        if 30 < peak_t < 55:
            elements.append(ParticleBurst(peak_t, peak_t + 2, 
                            (np.random.randint(200, 1720), np.random.randint(200, 880)),
                            30, COLORS['accent_cyan']))
    
    # ---- SECTION 4: ECOSYSTEM / INTEGRATIONS (55-80s) ----
    integrations = [
        ("Pollinations AI", 55.0, COLORS['accent_cyan']),
        ("OpenAI / GPT-Image", 57.1, COLORS['accent_orange']),
        ("Microsoft Trellis-3D", 59.2, COLORS['accent_green']),
        ("FFmpeg MCP", 61.4, COLORS['accent_cyan']),
        ("Exa Search", 63.5, COLORS['accent_orange']),
        ("Composio Connectors", 65.6, COLORS['accent_green']),
        ("Computer MCP", 67.7, COLORS['accent_cyan']),
        ("Ask Jev MCP", 69.8, COLORS['accent_orange']),
    ]
    
    for i, (name, start_t, color) in enumerate(integrations):
        angle = (i / len(integrations)) * 2 * math.pi
        radius = 350
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        
        # Connection line from center
        elements.append(GeometricShape(start_t, start_t + 2.0, 'line', (center_x, center_y), radius, color,
                           animation_type='fade_scale', rotation=math.degrees(angle)))
        
        # Node
        elements.append(GeometricShape(start_t + 0.2, start_t + 3.0, 'circle', (x, y), 40, color,
                           animation_type='fade_scale'))
        
        # Label
        elements.append(TextReveal(name, start_t + 0.3, start_t + 3.0, (x, y + 70), 20, color,
                      font_weight='regular', animation_type='fade_slide_up'))
    
    # Central pulsing core during this section
    for peak_t in peak_times:
        if 55 < peak_t < 80:
            elements.append(GeometricShape(peak_t, peak_t + 1.5, 'ring', (center_x, center_y), 100, COLORS['accent_cyan'],
                               animation_type='pulse'))
    
    # ---- SECTION 5: VISION / FUTURE (80-100s) ----
    vision_text = [
        ("Give Agents", 81.6, center_y - 80),
        ("Their Own", 84.0, center_y - 20),
        ("Identity", 86.5, center_y + 40),
    ]
    
    for text, start_t, y_pos in vision_text:
        elements.append(TextReveal(text, start_t, min(start_t + 10, 100), (center_x, y_pos), 72, COLORS['fg_white'],
                      font_weight='light', animation_type='word_by_word'))
        # Glow ring
        elements.append(GeometricShape(start_t, start_t + 3.0, 'ring', (center_x, y_pos), 250, COLORS['accent_cyan'],
                           animation_type='fade_scale'))
    
    # Landscape suggestion - horizontal line expanding
    elements.append(GeometricShape(89.3, 95, 'line', (center_x, center_y + 150), 600, COLORS['accent_orange'],
                       animation_type='fade_scale', rotation=0))
    
    # ---- SECTION 6: FINALE / LOGO (100-108s) ----
    # Final logo lockup
    elements.append(TextReveal("NEWE" + "RA", 100.0, duration, (center_x, center_y - 40), 100, COLORS['fg_white'],
                  font_weight='bold', animation_type='scale_in'))
    elements.append(TextReveal("AI AGENT", 100.5, duration, (center_x, center_y + 50), 36, COLORS['accent_cyan'],
                  font_weight='light', animation_type='fade_slide_up'))
    
    # Final particle burst
    elements.append(ParticleBurst(103.2, duration, (center_x, center_y), 120, COLORS['accent_cyan']))
    elements.append(ParticleBurst(106.6, duration, (center_x, center_y), 120, COLORS['accent_orange']))
    
    # Tagline
    elements.append(TextReveal("The Future of Autonomous AI", 104.0, duration, (center_x, center_y + 120), 28, COLORS['fg_gray'],
                  font_weight='regular', animation_type='fade_slide_up'))
    
    return elements

# ============================================================
# RENDER PIPELINE
# ============================================================

def render_frame(t, elements):
    """Render a single frame at time t by compositing all active elements."""
    # Start with base background
    frame = create_radial_gradient(WIDTH, HEIGHT, COLORS['bg_black'], COLORS['bg_dark'])
    frame = frame.convert('RGBA')
    
    # Composite all active elements
    for elem in elements:
        elem_frame = elem.get_frame(t)
        if elem_frame is not None:
            # Ensure frame is correct size
            from PIL import Image as PILImage
            if elem_frame.shape[0] != HEIGHT or elem_frame.shape[1] != WIDTH:
                # Resize if needed
                elem_img = PILImage.fromarray(elem_frame, 'RGBA' if elem_frame.shape[2] == 4 else 'RGB')
                elem_img = elem_img.resize((WIDTH, HEIGHT), PILImage.LANCZOS)
                elem_frame = np.array(elem_img.convert('RGBA'))
            
            elem_img = PILImage.fromarray(elem_frame, 'RGBA')
            frame = Image.alpha_composite(frame, elem_img)
    
    return frame.convert('RGB')

def make_frame(t):
    """MoviePy frame function."""
    frame = render_frame(t, all_elements)
    return np.array(frame)

# Create all elements
print("Creating scene elements...")
all_elements = create_scene_elements()
print(f"Total elements: {len(all_elements)}")

# Create video clip
print("Creating video clip...")
video_clip = VideoClip(make_frame, duration=duration)

# Add audio
audio_clip = AudioFileClip("ptasinski - life force (ft. RJ Pasin)_128k.mp3")
video_clip = video_clip.set_audio(audio_clip)

# Write output
print("Rendering video (this will take a while)...")
output_path = "newera_ai_agent_intro.mp4"
video_clip.write_videofile(output_path, fps=FPS, codec='libx264', audio_codec='aac',
                          preset='medium', bitrate='8000k', threads=4)

print(f"Video saved to {output_path}")
