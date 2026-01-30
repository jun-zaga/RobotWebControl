"""
Robot control layer:
- independent of Flask
- clamps happen in Flask, but you can clamp again here if you want
- replace prints with Maestro / GPIO / motor driver calls
"""

PHRASES = {
    1: "Hello, Hunter.",
    2: "Hunter is so cool.",
    3: "Please do not touch my wheels.",
    4: "Hunter is the greatest."
}

def drive(l: float, r: float) -> None:
    # l, r expected in [-1, 1]
    print(f"[drive] l={l:.2f} r={r:.2f}")
    # TODO: map to PWM/target units, enforce safe limits, send to motors

def head_pan(pan: float) -> None:
    # pan expected in [0, 1]
    print(f"[head_pan] {pan:.2f}")
    # TODO: map to servo range and command Maestro

def head_tilt(tilt: float) -> None:
    # tilt expected in [0, 1]
    print(f"[head_tilt] {tilt:.2f}")
    # TODO: map to servo range and command Maestro

def waist(pos: float) -> None:
    # pos expected in [0, 1]
    print(f"[waist] {pos:.2f}")
    # TODO: map to servo range and command Maestro

def stop() -> None:
    print("[stop] wheels -> 0, hold servos")
    # TODO: send wheel neutral / motor stop. Optionally center servos.

def say(phrase_id: int) -> bool:
    phrase = PHRASES.get(phrase_id)
    if not phrase:
        return False
    print(f"[say] {phrase}")
    # TODO: call TTS (espeak / pyttsx3) or play audio file
    return True
