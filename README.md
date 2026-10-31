# Flappy Bird (Pygame)

A simple Flappy Bird clone made with Python and Pygame for a game development course.
It runs on desktop and in the browser (built with pygbag).

## Controls
- SPACE / left click / tap: flap
- ESC: quit (desktop only)

## Run on desktop
```
pip install pygame-ce
python main.py
```

## Build for the web (pygbag)
```
pip install pygbag
pygbag --build .
```
The web version is created in `build/web`.
Use `pygbag --archive .` to also create `build/web.zip` for itch.io.

## Play on Windows
Double click `play.bat`. It installs pygame-ce the first time and then runs `main.py`
(you need Python installed, with "Add python.exe to PATH" ticked).
Double click `create_shortcut.bat` once to get a "Flappy Bird" shortcut with the bird icon
(in this folder and on the Desktop).
The best score is saved in `%APPDATA%\FlappyBird\highscore.txt`.

## Files
- `main.py` - the whole game
- `images/` - bird animation (`bird_sheet.png`), pipes, clouds, ground and the moving sky
- `play.bat` - double click to play on Windows
- `create_shortcut.bat`, `icon.ico` - makes a shortcut with the bird icon
- `sounds/` - background music, flap / score / hit / game over sounds (.ogg)
