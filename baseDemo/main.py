import tkinter as tk
import socket
import pygame
from pygame.locals import *

TCP_IP = '192.168.1.100'
TCP_PORT = 8080

# Create a tkinter window
window = tk.Tk()
window.title("Motor Control")
window.geometry("1400x700")

# Create sliders for motor values
motor_sliders = []
for i in range(1, 9):
    slider = tk.Scale(window, from_=0, to=100,
                      orient=tk.HORIZONTAL, label=f"Motor {i}")
    slider.pack()
    motor_sliders.append(slider)

# Initialize Pygame and Joystick
pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
else:
    print("No joystick connected")

continuous_sending = False

default_motor_values = [50] * len(motor_sliders)
joystick_invert = [False, False, False, False]
joystick_deadzone = 0.1
joystick_offsets = [0.0, 0.0, 0.0, 0.0]


def send_motor_values(default_values=False):
    # Read the current slider values or use default values
    motor_values = default_motor_values if default_values else [
        slider.get() for slider in motor_sliders]

    # Create a TCP socket connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TCP_IP, TCP_PORT))

    # Format the motor values as a comma-separated string
    motor_string = ",".join(str(value) for value in motor_values)

    try:
        # Send the motor values over the socket
        sock.sendall(motor_string.encode('utf-8'))

        # Receive the response from the server
        response = sock.recv(1024)
        print(f"Received response: {response.decode('utf-8')}")

        # Update the debug output
        debug_output.delete(1.0, tk.END)
        debug_output.insert(tk.END, f"Sent motor values: {motor_string}")

    except Exception as e:
        print(f"Error occurred: {str(e)}")

    finally:
        # Close the socket connection
        sock.close()


# Create a button to send motor values
send_button = tk.Button(window, text='Send Motor Values',
                        command=send_motor_values)
send_button.pack()

# Create a text widget for debug output
debug_output = tk.Text(window, height=4, width=40)
debug_output.pack()


def update_debug_output(dummy_arg=None):
    # Read the current slider values
    motor_values = [slider.get() for slider in motor_sliders]

    # Update the debug output
    debug_output.delete(1.0, tk.END)
    debug_output.insert(tk.END, f"Motor values: {motor_values}")


# Update the debug output whenever the slider values change
for slider in motor_sliders:
    slider.config(command=update_debug_output)


def apply_deadzone_and_offsets(axis_values):
    global joystick_deadzone, joystick_offsets, joystick_invert

    adjusted_values = []
    for value, offset, invert in zip(axis_values, joystick_offsets, joystick_invert):
        adjusted_value = value + offset
        if invert:
            adjusted_value = -adjusted_value
        if abs(adjusted_value) < joystick_deadzone:
            adjusted_value = 0.0
        adjusted_values.append(adjusted_value)

    return adjusted_values


def show_default_values_window():
    def update_default_values(dummy_arg=None):
        global default_motor_values
        default_motor_values = [slider.get() for slider in default_sliders]

    default_values_window = tk.Toplevel(window)
    default_values_window.title("Adjust Default Motor Values")

    default_sliders = []
    for i in range(1, 9):
        slider = tk.Scale(default_values_window, from_=0, to=100, orient=tk.HORIZONTAL,
                          label=f"Motor {i}", command=update_default_values)
        slider.set(default_motor_values[i - 1])
        slider.pack()
        default_sliders.append(slider)


menu_bar = tk.Menu(window)
window.config(menu=menu_bar)

options_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Options", menu=options_menu)
options_menu.add_command(label="Adjust Default Motor Values",
                         command=show_default_values_window)


def update_motor_values_from_joystick():
    # Read the joystick axes

    if pygame.joystick.get_count() > 0:
        raw_axis_values = [joystick.get_axis(i) for i in range(4)]
    else:
        raw_axis_values = [0, 0, 0, 0]

    # Apply deadzone and offsets
    adjusted_axis_values = apply_deadzone_and_offsets(raw_axis_values)

    strafe, vertical, rotation, forward_reverse = adjusted_axis_values

    default_motor_values = [
        int(49 + 50 * (forward_reverse - strafe - vertical + rotation)  * -1),  # Front-left motor
        int(47 + 50 * (forward_reverse + strafe - vertical - rotation)  * -1),  # Front-right motor
        int(50 + 50 * (forward_reverse - strafe - vertical + rotation)),  # Rear-left motor
        int(50 + 50 * (forward_reverse + strafe - vertical - rotation)),  # Rear-right motor
        int(46 + 50 * (forward_reverse - strafe + vertical + rotation) * -1),  # Front-left motor (bottom)
        int(49 + 50 * (forward_reverse + strafe + vertical + rotation) * -1),  # Front-right motor (bottom)
        int(47 + 50 * (forward_reverse - strafe + vertical + rotation)),  # Rear-left motor (bottom)
        int(47 + 50 * (forward_reverse + strafe + vertical + rotation)),  # Rear-right motor (bottom)
    ]

    # default_motor_values = [50 + int(50 * axis_value)
    #                         for axis_value in adjusted_axis_values]

    # Update the sliders with the new motor values
    for slider, value in zip(motor_sliders, default_motor_values):
        slider.set(value)

    # Update the debug output
    update_debug_output()


def show_joystick_settings_window():
    def update_joystick_settings(dummy_arg=None):
        global joystick_deadzone, joystick_offsets, joystick_invert
        joystick_deadzone = deadzone_slider.get()
        joystick_offsets = [slider.get() for slider in offset_sliders]
        joystick_invert = [var.get() for var in invert_vars]

    joystick_settings_window = tk.Toplevel(window)
    joystick_settings_window.title("Joystick Settings")

    deadzone_slider = tk.Scale(joystick_settings_window, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL,
                               label="Deadzone", command=update_joystick_settings)
    deadzone_slider.set(joystick_deadzone)
    deadzone_slider.pack()

    offset_sliders = []
    for i in range(4):
        slider = tk.Scale(joystick_settings_window, from_=-1, to=1, resolution=0.01, orient=tk.HORIZONTAL,
                          label=f"Offset for Axis {i}", command=update_joystick_settings)
        slider.set(joystick_offsets[i])
        slider.pack()
        offset_sliders.append(slider)

    invert_vars = []
    for i in range(4):
        var = tk.BooleanVar()
        var.set(joystick_invert[i])
        check = tk.Checkbutton(joystick_settings_window, text=f"Invert Axis {i}", variable=var,
                               command=update_joystick_settings)
        check.pack()
        invert_vars.append(var)


# Add a menu option to show the joystick settings window
options_menu.add_command(label="Joystick Settings",
                         command=show_joystick_settings_window)


def show_joystick_visualization_window():
    def update_joystick_visualization():
        # Read the joystick axes
        raw_axis_values = [joystick.get_axis(i) for i in range(4)]

        # Apply deadzone and offsets
        adjusted_axis_values = apply_deadzone_and_offsets(raw_axis_values)

        # Update the joystick visualization
        left_stick_x, left_stick_y, right_stick_x, right_stick_y = adjusted_axis_values
        left_stick_coords = (250 + left_stick_x * 100,
                             250 - left_stick_y * 100)
        right_stick_coords = (750 + right_stick_x * 100,
                              250 - right_stick_y * 100)

        canvas.coords(left_stick_indicator, left_stick_coords[0] - 10, left_stick_coords[1] - 10,
                      left_stick_coords[0] + 10, left_stick_coords[1] + 10)
        canvas.coords(right_stick_indicator, right_stick_coords[0] - 10, right_stick_coords[1] - 10,
                      right_stick_coords[0] + 10, right_stick_coords[1] + 10)

        # Schedule the next update
        visualization_window.after(100, update_joystick_visualization)

    visualization_window = tk.Toplevel(window)
    visualization_window.title("Joystick Visualization")

    canvas = tk.Canvas(visualization_window, width=1000, height=500)
    canvas.pack()

    # Draw left stick area
    canvas.create_oval(150, 150, 350, 350, outline="black")
    canvas.create_oval(225, 225, 275, 275, outline="black", dash=(2, 2))
    left_stick_indicator = canvas.create_oval(240, 240, 260, 260, fill="black")

    # Draw right stick area
    canvas.create_oval(650, 150, 850, 350, outline="black")
    canvas.create_oval(725, 225, 775, 275, outline="black", dash=(2, 2))
    right_stick_indicator = canvas.create_oval(
        740, 240, 760, 260, fill="black")

    update_joystick_visualization()


# Add a menu option to show the joystick visualization window
options_menu.add_command(label="Joystick Visualization",
                         command=show_joystick_visualization_window)


def toggle_continuous_sending():
    global continuous_sending
    continuous_sending = not continuous_sending


toggle_send_button = tk.Button(
    window, text="Start/Stop Continuous Sending", command=toggle_continuous_sending)
toggle_send_button.pack()


def stop_and_send_defaults():
    global continuous_sending
    continuous_sending = False
    send_motor_values(default_values=True)


stop_button = tk.Button(
    window, text="Stop and Send Defaults", command=stop_and_send_defaults)
stop_button.pack()

while True:
    window.update_idletasks()
    window.update()

    # Process Pygame events
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    # Update motor values from joystick input
    update_motor_values_from_joystick()

    # Continuously send motor values if enabled
    if continuous_sending:
        send_motor_values()
