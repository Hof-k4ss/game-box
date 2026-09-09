# Keyboard-first layout

GameBox is intended to be usable without controllers. EmulatorJS provides a Controls menu where the keyboard bindings can be changed per core/player.

Recommended starting layout for one shared keyboard:

```text
P1                         P2
W A S D                    Arrow keys
J = B / primary            Numpad 1 = B / primary
K = A / secondary          Numpad 2 = A / secondary
U = Y                      Numpad 4 = Y
I = X                      Numpad 5 = X
Enter = Start              Numpad Enter = Start
Right Shift = Select       Numpad 0 = Select
```

The exact EmulatorJS key identifier can differ by browser and keyboard layout, so use Menu -> Controls after launching a game and verify both players before starting a multiplayer session.

This model is **same-browser multiplayer**: several players use the same emulator instance and the same physical keyboard. It does not require WebRTC/Netplay and therefore remains compatible with a fully isolated LAN.

Good candidates are local multiplayer games whose original console/arcade core supports multiple simultaneous inputs, such as Bomberman, many fighting games, party games, beat-'em-ups and selected racing games. Mario Kart 64 should be tested with the exact ROM/core because N64 multiplayer/input behavior varies. Worms Armageddon is not a baseline supported browser title; use an emulated Worms-compatible release only when its platform/core is supported.
