import machine
import time
import st7735
import framebuf
from sysfont import sysfont

spi = machine.SPI(2, baudrate=20000000, polarity=0, phase=0, sck=machine.Pin(18), mosi=machine.Pin(23))
tft = st7735.ST7735(spi, rst=4, dc=2, cs=5)
tft.initr()
tft.fill(0)

b_onoff = machine.pin(X, machine.pin.IN, machine.pin.PULL_UP)
b_study = machine.pin(X, machine.pin.IN, machine.pin.PULL_UP)
b_break = machine.pin(X, machine.pin.IN, machine.pin.PULL_UP)

def load_image(filename):
    try:
        with open(filename, "rb") as f:
            return f.read()
    except:
        print(f"Could not find {filename}")
        return bytearray(128 * 160 * 2) # Return empty if file missing

# loading the 4 images
bg_data = load_image("bg.bin")
idle_data = load_image("pixil-frame-0-10.bin")
study_data = load_image("study.bin")
tired_data = load_image("tired.bin")

fb_bg = framebuf.FrameBuffer(bg_data, 128, 160, framebuf.RGB565)
fb_idle = framebuf.FrameBuffer(idle_data, 128, 160, framebuf.RGB565)
fb_study = framebuf.FrameBuffer(study_data, 128, 160, framebuf.RGB565)
fb_tired = framebuf.FrameBuffer(tired_data, 128, 160, framebuf.RGB565)



#modes are: idle (when doing nothing), study (when locked in), break (when pomodoro timer break), tired (when pomodoro timer runs out of study time)
mode = "idle"
study_s = 0
break_s = 300 #counts down
total_study = 0
happiness = 100

display_on = True
last_tick = time.ticks_ms()
last_bpress = time.ticks_ms()

#secods to minutes and seconds
#def format_time(seconds):
#    m = seconds // 60
#    s = seconds % 60
#    return "{:02d}:{:02d}".format(m, s)


def draw_screen():
    if not display_on:
        return
    tft.blit(fb_bg, 0, 0)

    current_pet = fb_idle
    if mode == "study":
        current_pet = fb_tired if study_s >= 1800 else fb_study
    elif mode == "break":
        current_pet = fb_idle if break_s <= 0 else fb_tired
    
    bob = 3 if (time.ticks_ms() // 500) % 2 == 0 else 0
    tft.blit(current_pet, 44, 70 - bob)

    if mode == "study":
        m, s = divmod(study_s, 60)
        tft.text(10, 10, f"study time: {m:02d}:{s:02d}", 0xFFFF, sysfont)
        if study_s >= 1800:
            tft.text(10, 25, "im tired :(", 0xFFFF, sysfont)
    elif mode == "break":
        m, s = divmod(break_s, 60)
        tft.text(10, 10, f"break: {m:02d}:{s:02d}", 0xFFFF, sysfont)
    else:
        tft.text(10, 10, ":3", 0xFFFF, sysfont)
        m, s = divmod(total_study, 60)
        tft.text(10, 140, f"total: {m:02d}:{s:02d}", 0xFFFF, sysfont)
    
    tft.rect(10, 150, 108, 6, 0xFFFF)
    tft.fillrect(11, 151, int(happiness * 1.06)),

#main loop
while True:
    now = time.ticks_ms()

    #buttons
    if time.ticks_diff(now, last_bpress) > 300:
        if not b_onoff.value():
            display_on = not display_on
            if not display_on: tft.fill(0)
            last_bpress = now
        elif not b_study.value() and display_on:
            if mode == "break":
                mode = "study"
            else:
                mode = "break"
                break_s = 300
            last_bpress = now
    
    if time.ticks_diff(now, last_tick) >= 1000:
        last_tick = now

        if mode == "study":
            study_s += 1
            #if tired after 30min of study, happiness decreases until 0 in the course of 15 mins (900s)
            if study_s > 1800:
                happiness = max(0, happiness - (100/900))

        elif mode == "break":
            if break_s > 0:
                break_s -= 1
                #happiness gain to 100, during 5 mins (300s)
                happiness = min(100, happiness + (100 / 300))
            else:
                total_study += study_s
                study_s = 0
                happiness = 100
                mode = "idle"
        
        draw_screen()
    
    time.sleep(0.1)


#(my) prog logic:
#i set up the hardware: display and buttons <- and define these
#i define framebuffers for the the bg and the 3 states: idle, study, tired
#i define the modes:
#idle: neutral, hangs out, display tot study time
#study: locked in, displays study time as a countup
#tired: pomodoro timer break, displays break time as a countdown
#i use a drawing mode, so theres a bg and stuff is layered on it
#i use a bobbing anim that shifts the pet by 3px every 500ms
#i have a rectangle with an inner section that shows happiness fullness
#i have a main loop:
#checks for buttons, but avoids double presses
#time tracks:
#study mode adds to study_s
#at 30min happiness gradually decreases
#in break mode happiness regains, once 5 mins are up it returns to the idle stage and displays tot study time
#screen refreshes every second (draw.screen())