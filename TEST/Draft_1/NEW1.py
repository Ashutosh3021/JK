import plotly.graph_objects as go
import numpy as np

fig = go.Figure()

# ─────────────────────────────────────────────
# PHYSICAL ENCLOSURE  (6 cm W × 4 cm H × 4 cm D)
# scaled 1 unit = 1 cm, centred at origin
# ─────────────────────────────────────────────
W, H, D = 6, 4, 4          # outer box dimensions
TH = 0.25                  # wall thickness

def box_edges(x0, x1, y0, y1, z0, z1, color='rgba(200,30,30,0.6)', width=3):
    """Return 12 edges of a box as a single Scatter3d trace."""
    verts = [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
             (x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
    edges = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),
             (0,4),(1,5),(2,6),(3,7)]
    xs, ys, zs = [], [], []
    for a, b in edges:
        xs += [verts[a][0], verts[b][0], None]
        ys += [verts[a][1], verts[b][1], None]
        zs += [verts[a][2], verts[b][2], None]
    return go.Scatter3d(x=xs, y=ys, z=zs, mode='lines',
                        line=dict(color=color, width=width),
                        showlegend=False, hoverinfo='skip')

def filled_face(corners, color, opacity=0.35, name=''):
    """Filled quad face via Mesh3d."""
    x = [c[0] for c in corners]
    y = [c[1] for c in corners]
    z = [c[2] for c in corners]
    return go.Mesh3d(x=x, y=y, z=z,
                     i=[0,0], j=[1,2], k=[2,3],
                     color=color, opacity=opacity,
                     name=name, showlegend=bool(name),
                     hoverinfo='name' if name else 'skip')

# ── Outer red body ──────────────────────────────
x0, x1 = -W/2, W/2
y0, y1 = -D/2, D/2
z0, z1 = 0, H
fig.add_trace(box_edges(x0, x1, y0, y1, z0, z1,
              color='rgba(220,30,30,0.9)', width=4))

# Filled side panels (red body)
for corners, n in [
    ([(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1)], 'Body Front Face'),
    ([(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)], ''),
    ([(x0,y0,z0),(x0,y1,z0),(x0,y1,z1),(x0,y0,z1)], ''),
    ([(x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1)], ''),
    ([(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0)], ''),
    ([(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)], ''),
]:
    fig.add_trace(filled_face(corners, 'red', opacity=0.18, name=n))

# ── TFT Display on front face (y = y0) ─────────────
DW, DH = 3.5, 2.5          # display width & height
DX0, DX1 = -DW/2, DW/2
DZ0, DZ1 = (H - DH)/2, (H + DH)/2
disp_corners = [(DX0,y0,DZ0),(DX1,y0,DZ0),(DX1,y0,DZ1),(DX0,y0,DZ1)]
fig.add_trace(filled_face(disp_corners, 'cyan', opacity=0.85, name='TFT Display (ST7789 / ILI9341)'))
fig.add_trace(box_edges(DX0, DX1, y0-0.01, y0, DZ0, DZ1,
              color='rgba(0,200,255,1.0)', width=3))
fig.add_trace(go.Scatter3d(
    x=[0], y=[y0-0.05], z=[H/2],
    mode='text', text=['📺 TFT Display'],
    textfont=dict(size=11, color='cyan'),
    showlegend=False, hoverinfo='skip'))

# ─────────────────────────────────────────────
# INTERNAL COMPONENT POSITIONS
# ─────────────────────────────────────────────
# Slightly inside the box (y > y0+TH, y < y1-TH)
# z=0.4 → bottom layer, z=2.5 → middle, z=3.5 → top

components = {
    'ESP32-S3\n(MCU + WiFi/BT)':  {'pos': [0.0,  0.6,  2.0], 'color': 'royalblue',  'size': 18},
    'TFT Display\n(ST7789 2.4")':  {'pos': [0.0, -1.6,  2.0], 'color': 'cyan',        'size': 13},
    'INMP441\nMicrophone':         {'pos': [-1.8,  1.4,  3.2], 'color': 'limegreen',   'size': 11},
    'PAM8302\nSpeaker Amp':        {'pos': [-1.8, -0.4,  3.2], 'color': 'orange',      'size': 11},
    'Speaker\n(1W 8Ω)':            {'pos': [-2.0,  0.6,  1.2], 'color': 'darkorange',  'size': 10},
    'Servo 1\n(Pan / Yaw)':        {'pos': [ 2.2,  0.6,  3.2], 'color': 'tomato',      'size': 11},
    'Servo 2\n(Tilt / Nod)':       {'pos': [ 2.2, -0.6,  3.2], 'color': 'tomato',      'size': 11},
    'LiPo 3.7V\n500 mAh':         {'pos': [ 0.0,  1.0,  0.5], 'color': 'mediumorchid','size': 13},
    'TP4056\nCharger IC':          {'pos': [ 1.6,  1.0,  0.5], 'color': 'deeppink',    'size': 10},
    'USB-C\nCharging Port':        {'pos': [ 2.8,  0.0,  0.5], 'color': 'silver',      'size': 9},
    'DS3231\nRTC Module':          {'pos': [-1.8,  0.6,  0.8], 'color': 'gold',        'size': 9},
    'WS2812B\nRGB LED':            {'pos': [ 0.8, -1.4,  3.5], 'color': 'lime',        'size': 8},
    'Level\nShifter 5V-3.3V':      {'pos': [ 1.8,  1.0,  1.8], 'color': 'lightblue',  'size': 8},
}

for name, data in components.items():
    px, py, pz = data['pos']
    fig.add_trace(go.Scatter3d(
        x=[px], y=[py], z=[pz],
        mode='markers+text',
        marker=dict(size=data['size'], color=data['color'],
                    symbol='circle',
                    line=dict(color='white', width=1)),
        text=[name], textposition='top center',
        textfont=dict(size=8),
        name=name.replace('\n', ' '),
        hoverinfo='name'
    ))

# ─────────────────────────────────────────────
# CONNECTIONS with labeled annotations
# ─────────────────────────────────────────────
connections = [
    ('ESP32-S3\n(MCU + WiFi/BT)', 'TFT Display\n(ST7789 2.4")',  'SPI: GPIO 5,18,19,23',    'cyan'),
    ('ESP32-S3\n(MCU + WiFi/BT)', 'INMP441\nMicrophone',          'I2S RX: GPIO 25,26,27',   'limegreen'),
    ('ESP32-S3\n(MCU + WiFi/BT)', 'PAM8302\nSpeaker Amp',         'I2S TX: GPIO 25,26,27',   'orange'),
    ('PAM8302\nSpeaker Amp',       'Speaker\n(1W 8Ω)',             'Analog Audio Out',         'darkorange'),
    ('ESP32-S3\n(MCU + WiFi/BT)', 'Servo 1\n(Pan / Yaw)',         'PWM GPIO 12',              'tomato'),
    ('ESP32-S3\n(MCU + WiFi/BT)', 'Servo 2\n(Tilt / Nod)',        'PWM GPIO 13',              'tomato'),
    ('LiPo 3.7V\n500 mAh',        'TP4056\nCharger IC',           'Battery Input',            'mediumorchid'),
    ('USB-C\nCharging Port',       'TP4056\nCharger IC',           'USB-C 5V In',              'silver'),
    ('TP4056\nCharger IC',         'ESP32-S3\n(MCU + WiFi/BT)',   '3.3V Regulated',           'royalblue'),
    ('TP4056\nCharger IC',         'Level\nShifter 5V-3.3V',      '5V Rail',                  'lightblue'),
    ('Level\nShifter 5V-3.3V',     'Servo 1\n(Pan / Yaw)',        '5V → Servo Power',         'tomato'),
    ('Level\nShifter 5V-3.3V',     'Servo 2\n(Tilt / Nod)',       '5V → Servo Power',         'tomato'),
    ('Level\nShifter 5V-3.3V',     'PAM8302\nSpeaker Amp',        '5V → Amp Power',           'orange'),
    ('ESP32-S3\n(MCU + WiFi/BT)', 'DS3231\nRTC Module',           'I2C: GPIO 21,22',          'gold'),
    ('ESP32-S3\n(MCU + WiFi/BT)', 'WS2812B\nRGB LED',             'GPIO 4 (LED Data)',         'lime'),
]

for start, end, label, color in connections:
    sp = components[start]['pos']
    ep = components[end]['pos']
    fig.add_trace(go.Scatter3d(
        x=[sp[0], ep[0]], y=[sp[1], ep[1]], z=[sp[2], ep[2]],
        mode='lines',
        line=dict(color=color, width=2),
        name=label,
        hoverinfo='text',
        text=[label, label],
        showlegend=False
    ))

# ─────────────────────────────────────────────
# DIMENSION ANNOTATIONS
# ─────────────────────────────────────────────
ann_style = dict(showarrow=False,
                 font=dict(size=11, color='white', family='Courier New Bold'))

annotations_3d = [
    dict(x=0, y=y1+0.3, z=H/2, text='← 6 cm →', **ann_style),
    dict(x=x1+0.3, y=0, z=H/2, text='4 cm', **ann_style),
    dict(x=x0-0.3, y=0, z=H/2, text='H=4cm', **ann_style),
]

# ─────────────────────────────────────────────
# WiFi / BT signal lines (decorative arcs)
# ─────────────────────────────────────────────
theta = np.linspace(0, np.pi/2, 20)
for r, alpha in [(0.6, 0.9), (1.0, 0.6), (1.4, 0.3)]:
    fig.add_trace(go.Scatter3d(
        x=r*np.cos(theta), y=[y1+0.1]*len(theta),
        z=H + r*np.sin(theta),
        mode='lines',
        line=dict(color=f'rgba(100,200,255,{alpha})', width=2),
        showlegend=False, hoverinfo='skip'
    ))
fig.add_trace(go.Scatter3d(
    x=[0], y=[y1+0.1], z=[H+1.6],
    mode='text', text=['📶 WiFi / Bluetooth'],
    textfont=dict(size=10, color='deepskyblue'),
    showlegend=False, hoverinfo='skip'))

# ─────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────
fig.update_layout(
    title=dict(
        text='🤖 AI Desktop Robot — Full 3D Circuit & Body Diagram',
        font=dict(size=18, color='white'),
        x=0.5
    ),
    paper_bgcolor='#0d0d1a',
    scene=dict(
        xaxis=dict(title='Width (cm)', range=[-4.5, 4.5],
                   backgroundcolor='#111122', gridcolor='#333355',
                   showbackground=True),
        yaxis=dict(title='Depth (cm)', range=[-2.8, 2.8],
                   backgroundcolor='#111122', gridcolor='#333355',
                   showbackground=True),
        zaxis=dict(title='Height (cm)', range=[-0.5, 6.0],
                   backgroundcolor='#111122', gridcolor='#333355',
                   showbackground=True),
        camera=dict(eye=dict(x=1.8, y=-2.2, z=1.6)),
        annotations=annotations_3d,
    ),
    legend=dict(
        bgcolor='rgba(20,20,40,0.85)',
        bordercolor='#444466',
        borderwidth=1,
        font=dict(color='white', size=9),
        x=1.0, y=0.98,
    ),
    width=1400,
    height=900,
    margin=dict(l=0, r=0, b=0, t=50),
    hovermode='closest',
)

# ─────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────
fig.write_html('ai_robot_circuit_3d_enhanced.html')
print("✅ Enhanced 3D diagram saved → ai_robot_circuit_3d_enhanced.html")
print()
print("📦 BILL OF MATERIALS")
print("─" * 45)
bom = [
    ("ESP32-S3 Dev Board",           "MCU + WiFi 802.11b/g/n + BT5 BLE"),
    ("2.4\" TFT ST7789 / ILI9341",  "240×320 colour display, SPI"),
    ("INMP441 Microphone",           "I2S MEMS mic, 3.3 V"),
    ("PAM8302 Amp + Speaker",        "1 W class-D amp, 8 Ω speaker"),
    ("MG90S Servo × 2",             "Pan + tilt, 5 V, 180°"),
    ("LiPo 500 mAh 3.7 V",          "Rechargeable battery"),
    ("TP4056 USB-C Charger",         "Li-Ion CC/CV charger IC"),
    ("DS3231 RTC",                   "Real-time clock, I2C, CR2032"),
    ("WS2812B RGB LED",              "Status / mood indicator, GPIO 4"),
    ("Logic Level Shifter",          "3.3 V ↔ 5 V for servo/amp"),
    ("USB-C port (breakout)",        "Charging input"),
    ("Red ABS/PLA enclosure",        "6 × 4 × 4 cm body"),
]
for part, desc in bom:
    print(f"  • {part:<35} {desc}")