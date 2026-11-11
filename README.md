# 🐾 Mouse Pet – An Interactive Desktop Companion

A fun, animated desktop pet that follows your mouse cursor around the screen! Choose your favourite animal, interact with it, change its appearance, and even play a little catch me if you can game.

This project is built entirely in Python using PyQt5 and Pygame. The pet stays on top of your desktop, follows your cursor, responds to mouse interactions, and comes with animated movements and sound effects.

## ✨ Features

### 🐶 Multiple Animal Characters
Choose between four different desktop pets:
- Dog 🐕
- Cat 🐈
- Duck 🦆
- Perry the Platypus

Each character has its own appearance, colour, and sound effects.

### 🖱️ Interactive Mouse Following
- The pet continuously follows your mouse cursor.
- Its direction changes depending on the cursor's position.
- Animated walking movements make the pet feel alive.
- The pet stays on top of other desktop windows.

### 😴 Sleep Mode
- Double-click the pet to send it to sleep.
- The pet walks towards its sleeping position.
- Sleeping animations and snoring sound effects are included.
- Double-click again to wake it up.

### 🏃 Flee Mode
- Hold the left mouse button on the pet for 3 seconds to activate Flee Mode.
- The pet starts running away from the cursor.
- If left undisturbed for 5 seconds, it goes to sleep.
- Catch the fleeing pet by keeping your cursor over it for approximately 1 second.

### 🎮 Catch me if you can Game
- Catching the fleeing pet increases your score.
- After reaching 5 points, something crazy happens.
- Only one clone is the real target.
- Find and catch the correct pet to bring everything back together!

### ⚙️ Customisation and Controls
- Adjust movement speed (1–15 px).
- Change the pet's colour using a colour picker.
- Adjust sound volume (10%–100%).
- Resize the pet using mouse scrolling.
- Close the application through the settings menu.

## 🎮 Controls

| Mouse Action | Function |
|---|---|
| Move cursor | Pet follows the cursor |
| Left-click | Interact with the pet |
| Hold left-click for 3 seconds | Activate Flee Mode |
| Double left-click | Sleep / Wake up |
| Right-click | Open settings menu |
| Hold right-click for 2 seconds | Open animal selection menu |
| Middle-click | Toggle resizing mode |
| Scroll mouse wheel | Increase / decrease pet size (in resizing mode) |

## 🛠️ Technologies & Libraries

The project uses the following Python libraries:

| Library | Purpose |
|---|---|
| PyQt5 | Desktop window, GUI, animations, drawing and mouse interactions |
| Pygame | Sound effects and audio playback |
| sys | Application execution and exit handling |
| math | Movement calculations, distance and animation |
| os | Audio file path handling |
| random | Random movement, clone positions and sound timing |

**Installation requirements:**

Only two external Python packages are required:

```bash
pip install PyQt5 pygame
```

The remaining modules are part of Python's standard library.

## 📂 Project Structure

Keep the Python file and audio folder together:

```text
Mouse-Pet/
│
├── Desktop_Pet.py
│
└── Mouse_Pet/
    ├── dwog.mp3
    ├── cat.mp3
    ├── dack.mp3
    ├── perry_the_platypus.mp3
    ├── snore.mp3
    ├── boom.mp3
    └── regen.mp3
```

The audio files are used for animal sounds, sleeping, explosion and regeneration effects.

## 🚀 How to Run

You can download or clone the complete repository and run it locally.

**1. Clone the repository**

```bash
git clone https://github.com/YOUR-USERNAME/Mouse-Pet.git
```

**2. Navigate to the project folder**

```bash
cd Mouse-Pet
```

**3. Install the required libraries**

```bash
pip install PyQt5 pygame
```

**4. Run the Python script**

```bash
python main.py
```

That's it! Your desktop pet should appear on your screen.

Alternatively, download the repository as a ZIP file, extract the folder, install the dependencies, and run the Python script.

**Important:** Keep the `Mouse_Pet` audio folder in its original location so that the sound effects can be loaded correctly.

## 🎨 Implementation

The desktop pet is implemented as a custom PyQt5 widget.

- `QPainter` is used to draw the animal characters and their animations.
- `QTimer` drives the movement and animation loop at approximately 30 FPS.
- `QPoint` manages the pet's screen position.
- Mouse event handlers detect clicks, double-clicks, scrolling and long presses.
- Pygame's mixer handles sound playback through dedicated audio channels.

The pet's behaviour is managed through different states, including:

- `FOLLOWING`
- `WALKING_TO_BED`
- `SLEEPING`
- `FLEEING`
- `FLEE_SLEEPING`
- `EXPLODING`
- `MERGING`

## 💡 About the Project

This project was created as a fun Python desktop application to explore GUI development, event handling, animation, mouse interaction, and audio integration.

It combines a virtual desktop companion with interactive behaviour and simple game mechanics, making your desktop a little more interesting!

---

⭐ If you like this project, feel free to star the repository!

🐾 Have fun with your new desktop companion!
